import torch, gc
import os, json, requests, dotenv, asyncio
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

from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
set_llm_cache(InMemoryCache())

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    return " ".join([doc.page_content.replace('\n', ' ') for doc in docs])

# Define model and tokenizer paths
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
model_path = os.path.join(app.MODEL_DIRECTORY, model_name)
tokenizer_path = os.path.join(app.TOKENIZER_DIRECTORY, model_name)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

# Set up quantization configuration
bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)

# Load model with quantization
model = AutoModelForCausalLM.from_pretrained(model_path, cache_dir= cache_dir, device_map="auto", quantization_config=bnb_config)

# Set up embeddings
embeder = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large", cache_folder=cache_dir)

# Set pad token for the tokenizer
tokenizer.pad_token = tokenizer.eos_token

# Define generation configuration
generation_config = GenerationConfig(
    max_new_tokens=1000,
    do_sample=True,
    bos_token_id=tokenizer.bos_token_id,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id
)

# Set up text generation pipeline
pipe = pipeline(
    "text-generation", 
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=128
)

# Set up HuggingFace pipeline
hf_pipe = HuggingFacePipeline(pipeline=pipe, model_kwargs={"generation_config": generation_config})

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
        retriever = vectorstore.as_retriever()

        # Define prompt template
        prompt = ChatPromptTemplate.from_template(
            template="Given the context: {context}, and the question: {question}, provide a short answer."
        )
        
        # Define RAG chain from documents
        rag_chain_from_docs = (
            RunnablePassthrough.assign(context=RunnablePick("context") | format_docs)
            | prompt
            | hf_pipe
            | StrOutputParser()
        )

        # Define the main RAG chain
        rag_chain = RunnableParallel(
            {"context": retriever, "question": RunnablePassthrough()}
        ).assign(answer=rag_chain_from_docs)
        
        # Invoke the RAG chain with the question
        result = rag_chain.invoke(question)

        # Extract relevant context
        relevant_context = result.get('context', [])
        formated_context = [element.page_content.replace('\n', ' ') for element in relevant_context]

        # Yield formatted context
        yield json.dumps({"context": formated_context}) + '\n'
        
        # Yield answer tokens one by one with a delay
        for token in result["answer"].split():
            yield json.dumps({"answer": token}) + '\n'
            await asyncio.sleep(0.1)

    # Clear GPU cache
    gc.collect()
    torch.cuda.empty_cache()
    
    # Return streaming response
    return StreamingResponse(answer_generator(), media_type="application/json")

# Main entry point for running the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
