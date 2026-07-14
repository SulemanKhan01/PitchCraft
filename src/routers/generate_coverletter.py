from fastapi import APIRouter ,HTTPException

from pydantic import BaseModel
from src.cover_letter.pipeline import generate_cover_letter_content


router = APIRouter(
    prefix="/api/generate",
    tags=["Generate"]
)

class GenerateRequest(BaseModel):
    jd_text: str



class GenerateResponse(BaseModel):
    generated_content : str
    num_chunks_used   : int 




@router.post("/cover-letter" , response_model = GenerateResponse)

async def generate_cover_letter(request : GenerateRequest):
    

    if not request.jd_text or not request.jd_text.strip():
        raise HTTPException(status_code = 400 , detail = "jd_text cannot be empty.")


    result = generate_cover_letter_content(request.jd_text)

    response = GenerateResponse(
        generated_content = result.generated_content,
        num_chunks_used   = result.num_chunks_used,
    )

    return response