from datetime import datetime
start = datetime.now()

import torch, gc
import os, json, asyncio, re
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline, GenerationConfig
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS, VectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables import RunnableParallel, RunnablePick
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.llms import HuggingFacePipeline
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import AsyncGenerator
import logging

#from langchain.globals import set_llm_cache
#from langchain_community.cache import InMemoryCache
#set_llm_cache(InMemoryCache())

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


gc.collect()
torch.cuda.empty_cache()
    
# Initialize FastAPI app
app = FastAPI()

# Define paths for uploads, models, and tokenizers
cache_dir = "/app/cache"
app.file_path = None
app.UPLOAD_DIRECTORY = "/app/rag-uploads"
app.MODEL_DIRECTORY = "/app/models"
app.TOKENIZER_DIRECTORY = "/app/tokenizers"

# Allow all origins for CORS
origins = ["*"]

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
if not os.path.exists(app.UPLOAD_DIRECTORY):
    os.makedirs(app.UPLOAD_DIRECTORY)

# Define a Pydantic model for query requests
class QueryRequest(BaseModel):
    query: str
    context: str = None

# Function to format documents
def format_docs(docs):
    formatted = "\n\n".join([f"Document {i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])
    return formatted


def tokenize_and_format(text):
    text = text.replace('\n\n', '<br/><br/>').replace('\n', '<br/>').replace(' ', '&nbsp;')
    tokens = re.findall(r'(<br\/><br\/>|<br\/>|&nbsp;|[^&<>]+)', text)
    
    return tokens

# Define model and tokenizer paths
# model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
# model_name = "microsoft/DialoGPT-medium"
#model_name = "mistralai/Mistral-7B-Instruct-v0.2"
#model_name = "mistralai/Mistral-7B-Instruct-v0.3"
#model_name = "microsoft/phi-2"

model_name = "unsloth/tinyllama-chat-bnb-4bit"
model_path = os.path.join(app.MODEL_DIRECTORY, model_name)
tokenizer_path = os.path.join(app.TOKENIZER_DIRECTORY, model_name)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

# Set up quantization configuration
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_use_double_quant=True,
    bnb_8bit_quant_type="nf4",
    bnb_8bit_compute_dtype=torch.float16
)

# Load model with quantization
model = AutoModelForCausalLM.from_pretrained(model_path, cache_dir= cache_dir, device_map="auto", quantization_config=bnb_config)

# Set up embeddings
embeder = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large", cache_folder=cache_dir)

# Set pad token for the tokenizer
tokenizer.pad_token = tokenizer.eos_token
terminators = [
                        tokenizer.eos_token_id,
                        tokenizer.convert_tokens_to_ids("<|eot_id|>")
                    ]


# Define generation configuration
generation_config = GenerationConfig(
    max_new_tokens=1000,  # Adjust based on your needs
    do_sample=False,
    num_beams=1,
    temperature=0.4,  # Adjust for creativity vs consistency
    top_k=50,
    top_p=0.95,
    repetition_penalty=1.2,
    bos_token_id=tokenizer.bos_token_id,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id
)

# Set up text generation pipeline
pipe = pipeline(
    model=model,
    tokenizer=tokenizer,
    task="text-generation",
    temperature=0.2,
    do_sample=True,
    repetition_penalty=1.1,
    return_full_text=False,
    max_new_tokens=1000,
    eos_token_id=terminators,

)

# Set up HuggingFace pipeline
hf_pipe = HuggingFacePipeline(pipeline=pipe, model_kwargs={"generation_config": generation_config})


end = datetime.now()

total_time = end - start

logger.info(f"Stet up time: {total_time}")
# Endpoint to upload a file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"UPLOADING FILE WITH NAME {file.filename}")
    file_location = os.path.join(app.UPLOAD_DIRECTORY, file.filename)
    app.file_path = file_location
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return {"filePath": file_location}

# Endpoint to retrieve answers from the document at a given path
@app.get("/retrieve_from_path")
async def retrieve_from_path(file_path: str = Query(...), question: str = Query(...)):
    
    # Generator to provide asynchronous response
    async def answer_generator() -> AsyncGenerator[str, None]:
        logger.info(f"RECEIVED REQUEST WITH FILE PATH {file_path} AND QUESTION {question}")
        
        # Load documents from the file
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
        chunks = text_splitter.split_documents(documents)
        
        # Create a FAISS vector store from the document chunks
        vectorstore = FAISS.from_documents(documents=chunks, embedding=embeder)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        # Define prompt template
        prompt = ChatPromptTemplate.from_template(
            """<|system|>
                You are an assistant designed to help with question-answering tasks. Use the following pieces of retrieved context to provide a concise and accurate answer to the question. Keep your response to a maximum of ten sentences.
                If you don't know the answer, just say "I do not know." Don't make up an answer.

                Context: {context}

                <|user|>
                Question: {question}

                <|assistant|>
                Answer (without repeating the labels or unnecessary text):
                """

        )

        

        rag_chain_from_docs = (
                RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
                | prompt
                | hf_pipe
                | StrOutputParser()
            )

        rag_chain = RunnableParallel(
                {"context": retriever, "question": RunnablePassthrough()}
            ).assign(answer=rag_chain_from_docs)
        result = rag_chain.invoke(question)


        relevant_context = result.get('context', [])
        formatted_context = []

        for element in relevant_context:
            context_tokens = tokenize_and_format(element.page_content)
            formatted_element = ''.join(context_tokens)
            formatted_context.append(formatted_element)
            
        yield json.dumps({"context": formatted_context})+ '\n'

        text = result["answer"]

        tokens = tokenize_and_format(text)
        
        for token in tokens:
            yield json.dumps({"answer": token}) + '\n'
            await asyncio.sleep(0.05)  # Adjust the sleep time as needed
    # Clear GPU cache
    gc.collect()
    torch.cuda.empty_cache()
    
    # Return streaming response
    return StreamingResponse(answer_generator(), media_type="application/json")

# Main entry point for running the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)