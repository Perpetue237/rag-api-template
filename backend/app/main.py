import os, json, requests
import dotenv, asyncio
from transformers import RagTokenizer, RagRetriever, RagTokenForGeneration
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

import logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



app = FastAPI()
app.file_path = None
app.UPLOAD_DIRECTORY = "/app/rag-uploads"

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
   
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"UPLAODING FILE WITH NAME {file.filename}")
    file_location = os.path.join(app.UPLOAD_DIRECTORY, file.filename)
    app.file_path = file_location
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return {"filePath": file_location}

 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)