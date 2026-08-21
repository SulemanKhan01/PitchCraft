"""
scraper_scheduler.py — APScheduler background job for auto-scraping Upwork.
Reuses _run_scraper_sync and _build_job directly from src.routers.jobs.
"""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.services.discord_notifier import send_job_alert

logger = logging.getLogger("scraper_scheduler")

# ── In-memory state ───────────────────────────────────────────────────────────
_scheduler_state = {
    "last_scraped_at": None,
    "is_running": False,
}
_scheduler_instance = None


async def auto_scrape_job():
    """Called by APScheduler every ~20 min (±5 min jitter = 15–25 min)."""
    if _scheduler_state["is_running"]:
        logger.info("⏭️  Skipping — previous scrape still running.")
        return

    _scheduler_state["is_running"] = True
    logger.info("🤖 Auto-scrape triggered by scheduler...")

    try:
        # ✅ Reuse existing functions — no duplication
        from src.routers.jobs import _run_scraper_sync, _build_job
        from database import SessionLocal
        from src.models.job import Job

        job_attributes = await asyncio.to_thread(_run_scraper_sync)

        db = SessionLocal()
        try:
            saved = skipped = 0
            if job_attributes:
                for data in job_attributes:
                    job_id_val = str(data.get("job_id", "")).strip()
                    if not job_id_val:
                        skipped += 1
                        continue
                    if db.query(Job).filter(Job.job_id == job_id_val).first():
                        skipped += 1
                        continue
                    job_obj = _build_job("auto-scheduler", data)
                    db.add(job_obj)
                    saved += 1
                    
                    # ── Send Discord Alert for new job ──────────────────────────────
                    budget_str = f"${job_obj.fixed_budget_amount}" if job_obj.fixed_budget_amount else f"${job_obj.hourly_min}-${job_obj.hourly_max}/hr"
                    send_job_alert(job_obj.title, budget_str, job_obj.url, job_obj.skills)
            db.commit()
            _scheduler_state["last_scraped_at"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"✅ Auto-scrape done. Saved: {saved}, Skipped: {skipped}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Auto-scrape failed: {e}")
    finally:
        _scheduler_state["is_running"] = False


def get_scheduler_state() -> dict:
    """Return current state + next run time pulled from APScheduler."""
    state = _scheduler_state.copy()
    if _scheduler_instance:
        job = _scheduler_instance.get_job("auto_scrape")
        state["next_scrape_at"] = job.next_run_time.isoformat() if (job and job.next_run_time) else None
    else:
        state["next_scrape_at"] = None
    return state


def create_scheduler() -> AsyncIOScheduler:
    global _scheduler_instance
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        auto_scrape_job,
        trigger=IntervalTrigger(minutes=20, jitter=300),  # 300s jitter = ±5 min
        id="auto_scrape",
        name="Upwork Auto Scraper",
        replace_existing=True,
    )
    _scheduler_instance = scheduler
    return scheduler
