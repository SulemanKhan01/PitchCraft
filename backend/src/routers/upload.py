from sys import prefix
from fastapi import APIRouter , UploadFile , File, HTTPException
import os
from src.pipeline.pipeline import process_pdf
from config import COLLECTION_NAME
import shutil


router = APIRouter(
    prefix = "/api/proposals",
    tags = ["Proposal"]
)

upload_dir = "data/raw_pdfs"
os.makedirs(upload_dir , exist_ok = True)

@router.post("/upload")
async def upload_proposal(file : UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400 , detail = "Only PDF files are allowed")


    file_path = os.path.join(upload_dir , file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file , buffer)
    
    try:
        result = process_pdf(file_path , collection_name = COLLECTION_NAME)


        return {
            "message": "Success! File processed.",
            "filename": file.filename,
            "category": result["category"],
            "chunks_created": result["chunks"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    # return {"filename": file.filename, "status": "Ready to process!!!!!!!"}