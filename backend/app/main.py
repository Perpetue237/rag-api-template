import os, json, requests
import dotenv, asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline, GenerationConfig

import torch

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS, VectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables import RunnableParallel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_community.llms import HuggingFacePipeline



from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from typing import AsyncGenerator

import logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



app = FastAPI()
app.file_path = None
app.UPLOAD_DIRECTORY = "/app/rag-uploads"
app.MODEL_DIRECTORY = "/app/models"
app.TOKENIZER_DIRECTORY = "/app/tokenizers"

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(app.UPLOAD_DIRECTORY):
    os.makedirs(app.UPLOAD_DIRECTORY)

class QueryRequest(BaseModel):
    query: str
    context: str = None
    
def format_docs(docs):
    return " ".join([doc.page_content.replace('\n', ' ') for doc in docs])

    
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
model_path = os.path.join(app.MODEL_DIRECTORY, model_name)
tokenizer_path = os.path.join(app.TOKENIZER_DIRECTORY, model_name)

# Load the model and tokenizer from the local directories
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained(model_path,
                                                device_map="auto",
                                                quantization_config=bnb_config)
embeder = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large", cache_folder="/app/cache")

tokenizer.pad_token = tokenizer.eos_token
generation_config = GenerationConfig(
            max_new_tokens=1000,
            do_sample=True,
            bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id)

pipe = pipeline(
            "text-generation", 
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=1000
        )
hf_pipe = HuggingFacePipeline(pipeline=pipe, model_kwargs={"generation_config": generation_config})



   
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"UPLAODING FILE WITH NAME {file.filename}")
    file_location = os.path.join(app.UPLOAD_DIRECTORY, file.filename)
    app.file_path = file_location
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return {"filePath": file_location}

@app.get("/retrieve_from_path")
async def retrieve_from_path(file_path: str = Query(...), question: str = Query(...)):
    
    async def answer_generator() -> AsyncGenerator[str, None]:
        logger.info(f"RECEIVED REQUEST WITH FILE PATH {file_path} AND QUESTION {question}")
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(
                                            documents = chunks,
                                            embedding = embeder
                                            )
        retriever = vectorstore.as_retriever()

        prompt = ChatPromptTemplate.from_template(
        template="Given the context: {context}, and the question: {question}, provide a detailed answer."
        )
        rag_chain_from_docs = (
                                RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
                                | prompt
                                | hf_pipe
                                | StrOutputParser()
                            )

        rag_chain = RunnableParallel(
                                {"context":retriever, "question": RunnablePassthrough()}
                            ).assign(answer=rag_chain_from_docs)
        result = rag_chain.invoke(question)

        relevant_context = result.get('context', [])
        formated_context = [element.page_content.replace('\n', ' ') for element in relevant_context]

        yield json.dumps({"context": formated_context})+ '\n'
        for token in result["answer"].split():
            yield json.dumps({"answer": token}) + '\n'
            await asyncio.sleep(0.1)

    return StreamingResponse(answer_generator(), media_type="application/json")
    

 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)