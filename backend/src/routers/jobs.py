"""
jobs.py — Endpoints to manage scraped Upwork jobs.

Endpoints:
    POST   /api/jobs/scrape       → Run scraper, save results directly to DB
    GET    /api/jobs/             → List all jobs for the current user
    PATCH  /api/jobs/{id}/status  → Toggle: "pending" ↔ "applied"
    DELETE /api/jobs/{id}         → Delete a single job
"""

import asyncio
import os
import sys

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from src.auth.clerk_auth import get_current_user_clerk
from src.models.job import Job

from src.services.scraper_scheduler import get_scheduler_state
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# Discord Webhook
from src.services.discord_notifier import send_job_alert







# ── Add execution/ to sys.path so upwork_core's internal bare imports resolve ─
# (upwork_core does: "import camoufox_utils", "from attr_extractor import ...")
# Those files live in the execution/ folder — they need to be on sys.path.
_EXECUTION_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "services",
                 "upwork_scraper", "execution")
)
if _EXECUTION_DIR not in sys.path:
    sys.path.insert(0, _EXECUTION_DIR)

# ── Default search params JSON (same file run_job_search.py uses) ─────────────
_DEFAULT_SEARCH_PARAMS = os.path.join(_EXECUTION_DIR, "data", "inputs", "default_upwork_search.json")

# Call run_workflow — exactly the same entry point as run_job_search.py
# This handles: loading upwork_scraper/.env, loading search params, calling upwork_core.main()
from src.services.upwork_scraper.execution.scrape_upwork import run_workflow as scrape_run_workflow

# Auto Apply on jobs
from src.services.cover_letter.pipeline import generate_cover_letter_content
from src.services.upwork_scraper.execution.apply_job import run_apply_workflow


def _run_scraper_sync():
    """
    Run scraper in a dedicated thread with a fresh ProactorEventLoop.
    This resolves the Windows Playwright subprocess error (NotImplementedError)
    when running inside Uvicorn/FastAPI.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            scrape_run_workflow(
                search_params_input=_DEFAULT_SEARCH_PARAMS,
                browser_type="camoufox",
                headless=True,
                max_workers=5,
                limit=10,
            )
        )
    finally:
        loop.close()

def _run_apply_sync(job_url: str) -> bool:
    """
    Run the apply workflow in a dedicated thread with a fresh ProactorEventLoop.
    Same pattern as _run_scraper_sync to avoid Windows Playwright blocking issues.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_apply_workflow(job_url, headless=True))
    finally:
        loop.close()



router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
)

# ── Type-cast helpers ─────────────────────────────────────────────────────────
_BOOL_FIELDS = {
    "payment_verified", "premium", "enterpriseJob",
    "phone_verified", "isContractToHire",
}
_INT_FIELDS = {
    "client_hires", "applicants", "numberOfPositionsToHire",
    "connects_required", "client_reviews",
    "buyer_stats_activeAssignmentsCount", "buyer_stats_totalJobsWithHires",
    "clientActivity_invitationsSent", "clientActivity_totalHired",
    "clientActivity_totalInvitedToInterview", "clientActivity_unansweredInvites",
    "buyer_jobs_openCount", "buyer_jobs_postedCount", "contractorTier",
}
_FLOAT_FIELDS = {
    "buyer_hire_rate_pct", "client_total_spent",
    "buyer_avgHourlyJobsRate_amount", "buyer_stats_hoursCount",
    "client_rating", "buyer_location_offsetFromUtcMillis",
    "hourly_max", "hourly_min",
}


def _safe(value, cast):
    """Cast a value safely — return None on any failure."""
    if value is None or str(value).strip() in ("", "nan", "None"):
        return None
    try:
        return cast(value)
    except (ValueError, TypeError):
        return None


def _build_job(user_id: str, data: dict) -> Job:
    """Map a scraper result dict → Job ORM object."""
    kwargs = {"user_id": user_id, "status": "pending"}

    for key, value in data.items():
        if not hasattr(Job, key):
            continue                               # ignore unknown columns
        if key in _BOOL_FIELDS:
            if isinstance(value, bool):
                kwargs[key] = value
            elif isinstance(value, str):
                kwargs[key] = value.lower() in ("true", "1", "yes")
            else:
                kwargs[key] = None
        elif key in _INT_FIELDS:
            kwargs[key] = _safe(value, int)
        elif key in _FLOAT_FIELDS:
            kwargs[key] = _safe(value, float)
        else:
            kwargs[key] = str(value).strip() if value is not None else None

    return Job(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class StatusUpdateRequest(BaseModel):
    status: str   # "pending" or "applied"


def _job_to_dict(j: Job) -> dict:
    return {
        "id":                  j.id,
        "status":              j.status,
        "scraped_at":          j.scraped_at.isoformat(),
        "job_id":              j.job_id,
        "title":               j.title,
        "description":         j.description,
        "url":                 j.url,
        "category_name":       j.category_name,
        "type":                j.type,
        "level":               j.level,
        "skills":              j.skills,
        "fixed_budget_amount": j.fixed_budget_amount,
        "hourly_min":          j.hourly_min,
        "hourly_max":          j.hourly_max,
        "duration":            j.duration,
        "client_country":      j.client_country,
        "client_rating":       j.client_rating,
        "client_reviews":      j.client_reviews,
        "applicants":          j.applicants,
        "connects_required":   j.connects_required,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/scrape", status_code=status.HTTP_200_OK)
async def scrape_and_save(
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Trigger the Upwork scraper and save results directly to DB.
    Calls scrape_upwork.run_workflow() — the same entry point as run_job_search.py.
    Credentials are loaded from upwork_scraper/.env automatically.
    Search params are loaded from default_upwork_search.json automatically.
    Skips duplicates by job_id.
    """
    user_id = current_user.get("sub", "anonymous")

    try:
        # Run in a separate thread with dedicated ProactorEventLoop (Windows Playwright safe)
        job_attributes = await asyncio.to_thread(_run_scraper_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")

    if not job_attributes:
        return {"message": "Scraper returned no jobs.", "saved": 0, "skipped": 0}

    saved   = 0
    skipped = 0

    for data in job_attributes:
        job_id_val = str(data.get("job_id", "")).strip()

        if not job_id_val:
            skipped += 1
            continue

        # De-duplicate — skip if already in DB
        if db.query(Job).filter(Job.job_id == job_id_val).first():
            skipped += 1
            continue

        job_obj = _build_job(user_id, data)
        db.add(job_obj)
        saved += 1
        # Send Discord alert
        budget_str = f"${job_obj.fixed_budget_amount}" if job_obj.fixed_budget_amount else f"${job_obj.hourly_min}-${job_obj.hourly_max}/hr"
        send_job_alert(job_obj.title, budget_str, job_obj.url, job_obj.skills)

    db.commit()
    return {
        "message": f"Done. {saved} new jobs saved, {skipped} skipped.",
        "saved":   saved,
        "skipped": skipped,
    }


@router.get("/")
def list_jobs(
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """Return all jobs in DB (newest first)."""
    user_id = current_user.get("sub", "anonymous")
    jobs = (
        db.query(Job)
        # .filter(
        #     (Job.user_id == user_id) |
        #     (Job.user_id == "local-dev-user") |
        #     (Job.user_id == "local-fallback-user") |
        #     (Job.user_id == "anonymous")
        # )

        # NEW — includes auto-scheduler jobs
        .filter(
            (Job.user_id == user_id) |
            (Job.user_id == "local-dev-user") |
            (Job.user_id == "local-fallback-user") |
            (Job.user_id == "anonymous") |
            (Job.user_id == "auto-scheduler")
        )

        .order_by(Job.scraped_at.desc())
        .limit(10)
        .all()
    )
    return [_job_to_dict(j) for j in jobs]


@router.patch("/{job_id}/status")
def update_status(
    job_id: str,
    request: StatusUpdateRequest,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """Toggle a job's status between 'pending' and 'applied'."""
    if request.status not in ("pending", "applied"):
        raise HTTPException(status_code=400, detail="Status must be 'pending' or 'applied'.")

    user_id = current_user.get("sub", "anonymous")
    job = db.query(Job).filter(
        Job.id == job_id,
        (Job.user_id == user_id) | (Job.user_id == "local-dev-user") | (Job.user_id == "local-fallback-user") | (Job.user_id == "anonymous")
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    job.status = request.status
    db.commit()
    db.refresh(job)
    return _job_to_dict(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """Delete a single job."""
    user_id = current_user.get("sub", "anonymous")
    job = db.query(Job).filter(
        Job.id == job_id,
        (Job.user_id == user_id) | (Job.user_id == "local-dev-user") | (Job.user_id == "local-fallback-user") | (Job.user_id == "anonymous")
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    db.delete(job)
    db.commit()


@router.get("/scraper-status")
def get_scraper_status():
    """
    Returns scheduler state for frontend timer display.
    { last_scraped_at, next_scrape_at, is_running }
    """
    state = get_scheduler_state()
    return {
        "last_scraped_at": state.get("last_scraped_at"),
        "next_scrape_at":  state.get("next_scrape_at"),
        "is_running":      state.get("is_running", False),
    }



@router.post("/{job_id}/apply", status_code=status.HTTP_200_OK)
async def apply_to_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_clerk),
    db: Session = Depends(get_db),
):
    """
    Phase 1: Generate a cover letter for the selected job, then navigate
    to the job URL and click the Apply button. Script exits after clicking.
    """
    user_id = current_user.get("sub", "anonymous")

    # Fetch the job from DB
    job = db.query(Job).filter(
        Job.id == job_id,
        (Job.user_id == user_id) |
        (Job.user_id == "local-dev-user") |
        (Job.user_id == "local-fallback-user") |
        (Job.user_id == "anonymous") |
        (Job.user_id == "auto-scheduler")
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if not job.url:
        raise HTTPException(status_code=400, detail="Job has no URL to navigate to.")

    if not job.description:
        raise HTTPException(status_code=400, detail="Job has no description to generate cover letter from.")

    # Step 1: Generate cover letter using existing pipeline
    try:
        result = generate_cover_letter_content(job.description)
        job.cover_letter = result.generated_content
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")

    # Step 2: Launch browser, login, navigate, click apply button
    try:
        success = await asyncio.to_thread(_run_apply_sync, job.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browser apply failed: {str(e)}")

    if not success:
        raise HTTPException(status_code=500, detail="Apply button was not found or could not be clicked.")

    return {
        "message": "Cover letter generated and apply button clicked successfully.",
        "job_id": job_id,
        "cover_letter": job.cover_letter,
    }
