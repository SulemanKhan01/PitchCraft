"""
apply_job.py — Browser automation script to navigate to a specific Upwork job URL
and click the primary action button (Apply Now / Buy Connects to apply).

Phase 1: Click the button and exit. No form filling.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from camoufox import AsyncCamoufox

# ── Resolve paths so local imports work ──────────────────────────────────────
execution_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(execution_dir)

if execution_dir not in sys.path:
    sys.path.insert(0, execution_dir)

# Load .env from upwork_scraper/
load_dotenv(os.path.join(parent_dir, '.env'))

try:
    from logger import Logger
    from camoufox_utils import login_and_solve, safe_goto, click_apply_button
except ImportError:
    from execution.logger import Logger
    from execution.camoufox_utils import login_and_solve, safe_goto, click_apply_button

logger = Logger(level="DEBUG").get_logger()


async def run_apply_workflow(job_url: str, headless: bool = True) -> bool:
    """
    Full Phase 1 workflow:
    1. Launch Camoufox browser
    2. Bypass Cloudflare and login
    3. Navigate to the job URL
    4. Click the apply button
    5. Close browser and return result
    """
    username = os.environ.get("UPWORK_USERNAME")
    password = os.environ.get("UPWORK_PASSWORD")

    if not username or not password:
        logger.error("UPWORK_USERNAME and UPWORK_PASSWORD must be set in upwork_scraper/.env")
        return False

    login_url  = "https://www.upwork.com/ab/account-security/login"
    search_url = "https://www.upwork.com/nx/find-work/"

    logger.info(f"🚀 Starting apply workflow for: {job_url}")

    async with AsyncCamoufox(
        headless=headless,
        geoip=True,
        humanize=True,
        i_know_what_im_doing=True,
        config={'forceScopeAccess': True},
        disable_coop=True
    ) as browser:

        context = await browser.new_context()
        page    = await context.new_page()

        # Step 1: Login + Cloudflare bypass (reuse existing function)
        logger.info("🔒 Logging in and solving Cloudflare...")
        page, context = await login_and_solve(
            page, context,
            username, password,
            search_url, login_url,
            credentials_provided=True
        )

        # Step 2: Navigate to the specific job URL
        logger.info(f"🌐 Navigating to job: {job_url}")
        page = await safe_goto(page, job_url, context, timeout=30000)

        # Small human delay after page loads
        await asyncio.sleep(2.5)

        # Step 3: Click the apply button and exit
        logger.info("🖱️ Attempting to click the apply button...")
        success = await click_apply_button(page, context)

        if success:
            logger.info("✅ Apply button clicked. Phase 1 complete. Closing browser.")
        else:
            logger.error("⚠️ Apply button was not found or could not be clicked.")

    return success
