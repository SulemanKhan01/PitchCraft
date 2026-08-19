from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional


from src.auth.clerk_auth import get_current_user_clerk
from src.services.website_generator.generator import generate_website_code
from src.services.website_generator.deployer import deploy_to_netlify

router = APIRouter(
    prefix= "/api/generate",
    tags= ['Website Generator']
)


class GenerateWebsiteRequest(BaseModel):
    job_description: str = Field(
        ..., 
        description="The client's job description or website requirements text.",
        min_length=10
    )
    custom_instructions: Optional[str] = Field(
        None, 
        description="Optional additional instructions (e.g. 'Use dark luxury theme')."
    )


@router.post("/website")
def generate_and_deploy_website(
    request: GenerateWebsiteRequest,
    current_user: dict = Depends(get_current_user_clerk)
):
    """
    Analyzes job description, generates a similar portfolio demo static website,
    deploys it to Netlify, and returns the live public URL.
    """
    user_id = current_user.get("sub", "anonymous")
    print(f"[WebsiteGenerator] Request received from User '{user_id}'")

    # 1. Build a prompt that asks AI for a SIMILAR demo portfolio website
    prompt = f"""Target Niche & Job Requirements:
{request.job_description}

Additional Instructions:
{request.custom_instructions or 'None'}

Goal:
Create a realistic, beautiful demo website in the SAME industry/niche to showcase as proof of work for this job.
Do NOT copy any client company names literally — create a fictional brand name for the demo site.
"""

    # 2. Call OpenAI code generator service
    try:
        files = generate_website_code(prompt)
    except ValueError as val_err:
        print(f"[WebsiteGenerator] Generation error: {val_err}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        print(f"[WebsiteGenerator] Unexpected generation error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate website code: {str(exc)}"
        )

    # 3. Deploy generated code to Netlify
    try:
        deployment_result = deploy_to_netlify(files)
    except Exception as exc:
        print(f"[WebsiteGenerator] Netlify deployment error: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Website was generated, but deployment to Netlify failed: {str(exc)}"
        )

    # 4. Return success payload
    return {
        "status": "success",
        "public_url": deployment_result["public_url"],
        "site_title": files.get("site_title", "Demo Website"),
        "site_id": deployment_result.get("site_id")
    }
