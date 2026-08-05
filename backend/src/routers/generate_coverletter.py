from fastapi import APIRouter ,HTTPException

import io

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.services.cover_letter.pipeline import generate_cover_letter_content
from src.services.cover_letter.pdf_generator import generate_minimal_pdf
from src.services.cover_letter.docx_generator import generate_minimal_docx


# for authentication
from fastapi import Depends
# from src.auth.dependencies import get_current_user  # JWT — replaced by Clerk
# from src.models.user import User                    # JWT — replaced by Clerk
from src.auth.clerk_auth import get_current_user_clerk


router = APIRouter(
    prefix="/api/generate",
    tags=["Generate"]
)

from typing import Optional

class GenerateRequest(BaseModel):
    jd_text: str
    writing_tone: Optional[str] = None
    agency_name: Optional[str] = None
    portfolio_url: Optional[str] = None
    signature_text: Optional[str] = None



class GenerateResponse(BaseModel):
    generated_content : str
    num_chunks_used   : int 


class PDFRequest(BaseModel):
    text: str
    pdf_template: Optional[str] = None





@router.post("/cover-letter" , response_model = GenerateResponse)
async def generate_cover_letter(request: GenerateRequest, current_user: dict = Depends(get_current_user_clerk)):
    

    if not request.jd_text or not request.jd_text.strip():
        raise HTTPException(status_code = 400 , detail = "jd_text cannot be empty.")


    result = generate_cover_letter_content(request.jd_text)

    response = GenerateResponse(
        generated_content = result.generated_content,
        num_chunks_used   = result.num_chunks_used,
    )

    return response


@router.post("/cover-letter/pdf")
async def download_pdf(request: PDFRequest, current_user: dict = Depends(get_current_user_clerk)):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty.")

    try:
        pdf_bytes = generate_minimal_pdf(request.text)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cover_letter.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.post("/cover-letter/docx")
async def download_docx(request: PDFRequest, current_user: dict = Depends(get_current_user_clerk)):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="text cannot be empty.")

    try:
        docx_bytes = generate_minimal_docx(request.text)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=cover_letter.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")