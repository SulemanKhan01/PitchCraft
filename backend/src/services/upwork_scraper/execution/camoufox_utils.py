import asyncio
import json
import os
import random
import re
import sys
from urllib.parse import urlparse, urlunparse

import requests
from camoufox import AsyncCamoufox
from playwright._impl._errors import TargetClosedError
from playwright.async_api import BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Import camoufox_captcha - handle both execution contexts
try:
    # Try importing from current directory (running from execution/)
    from camoufox_captcha import solve_captcha
except ImportError:
    # Fall back to importing from execution package (running from root)
    from execution.camoufox_captcha import solve_captcha

from logger import Logger

# Setup Logging
logger_obj = Logger(level="DEBUG")
logger = logger_obj.get_logger()

async def human_type(page: Page, selector: str, text: str):
    """
    Type text into an element with random delays to simulate human typing.
    """
    logger.debug(f"Human typing into {selector}...")
    element = page.locator(selector)
    await element.focus()
    await element.click(timeout=6000)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.15, 0.45))

async def safe_goto(
    page: Page,
    url: str,
    browser_context: BrowserContext,
    max_retries: int = 3,
    timeout: int = 30000,
    wait_untils: list[str] = ["domcontentloaded", "networkidle"]
) -> Page:
    """
    Safely navigate a Playwright page to a URL with retries and error handling.
    """
    last_exc = None

    for attempt in range(1, max_retries + 1):
        for wait_until in wait_untils:
            try:
                logger.debug(f"[Attempt {attempt}] goto({url}) waitUntil={wait_until}")
                response = await page.goto(url, timeout=timeout, wait_until=wait_until)
                logger.debug(f"[Attempt {attempt}] Navigation succeeded (waitUntil={wait_until})")
                # return working page
                return page  
            except TargetClosedError:
                logger.warning("Page or browser crashed. Creating new page...")
                try:
                    page = await browser_context.new_page()
                except Exception as create_exc:
                    logger.exception("Failed to create new page after crash.")
                    raise create_exc
            except Exception as e:
                last_exc = e
                logger.debug(f"[Attempt {attempt}] goto failed: {e}")

    logger.error(f"⚠️ Failed to navigate to {url} after {max_retries} attempts", exc_info=last_exc)
    raise last_exc

async def handle_security_question(page: Page, answer: str = "India") -> bool:
    """
    Detect and answer Upwork's post-login security question if it appears.
    Returns True if a question was found and answered, False otherwise.
    """
    try:
        # Upwork security question input field
        sec_input = page.locator('input[name="deviceAuth_answer"], input[placeholder*="answer"], input[id*="answer"], input[type="text"]').first
        if await sec_input.count() > 0 and await sec_input.is_visible(timeout=4000):
            logger.debug(f"Security question detected. Answering with: {answer}")
            await sec_input.fill(answer)
            await asyncio.sleep(random.uniform(0.8, 1.5))
            # Try clicking the submit/continue button
            try:
                submit_btn = page.locator('button[type="submit"], button:has-text("Continue"), button:has-text("Next"), button:has-text("Submit")').first
                await submit_btn.click(timeout=5000)
                logger.debug("Clicked security question submit button.")
            except Exception:
                await page.keyboard.press('Enter')
                logger.debug("Pressed Enter to submit security question.")
            await asyncio.sleep(random.uniform(2.0, 3.5))
            logger.debug("Security question answered.")
            return True
    except Exception as e:
        logger.debug(f"No security question found or error: {e}")
    return False

async def login_process(
    login_url: str,
    page: Page,
    context: BrowserContext,
    username: str,
    password: str,
    max_attempts: int = 2,
    initial_navigation: bool = True
) -> bool:
    """
    Automate the Upwork login process using Playwright, with robust retry logic.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            # Skip initial navigation if specified (e.g. we clicked "Log In" button)
            if not initial_navigation and attempt == 1:
                logger.debug("Skipping initial navigation (already on login flow)...")
            else:
                page = await safe_goto(page, login_url, context, timeout=60000)
            
            # --- Username Step ---
            await page.wait_for_selector('#login_username', timeout=10000)
            await human_type(page, '#login_username', username)
            logger.debug(f"Username entered: {username}")
            
            # Button Click Strategy (Username)
            try:
                # Attempt to click "Continue" button
                # Using specific ID from user request
                continue_btn = page.locator('#login_password_continue')
                # We attempt to click with a longer timeout. click() waits for visible/enabled/stable.
                await continue_btn.click(timeout=6000)
                logger.debug("Clicked 'Continue' button.")
            except Exception as e:
                logger.debug(f"Continue button click failed ({e}). Fallback to Enter.")
                await page.press('#login_username', 'Enter')

            await asyncio.sleep(random.uniform(2.5, 4.5))

            # --- Handle Google SSO accounts ---
            # If the account is linked to Google, Upwork shows "Continue with Google".
            # We click that button and handle the Google OAuth popup.
            google_btn = page.locator('button:has-text("Continue with Google"), a:has-text("Continue with Google")')
            try:
                is_google_sso = await google_btn.count() > 0 and await google_btn.is_visible(timeout=3000)
            except Exception:
                is_google_sso = False

            if is_google_sso:
                logger.debug("Google SSO detected. Clicking 'Continue with Google'...")
                try:
                    # Wait for the Google OAuth popup to open
                    async with context.expect_page() as popup_info:
                        await google_btn.click()
                    google_popup = await popup_info.value
                    logger.debug("Google OAuth popup opened. Waiting for Google login page...")
                    await google_popup.wait_for_load_state('domcontentloaded', timeout=15000)

                    # --- Google Email Step ---
                    try:
                        await google_popup.wait_for_selector('input[type="email"]', timeout=10000)
                        await google_popup.fill('input[type="email"]', username)
                        logger.debug(f"Google email entered: {username}")
                        await google_popup.click('#identifierNext, button:has-text("Next")')
                        await asyncio.sleep(random.uniform(2.0, 3.5))
                    except Exception as e:
                        logger.debug(f"Google email step: field not found or already filled ({e})")

                    # --- Google Password Step ---
                    try:
                        await google_popup.wait_for_selector('input[type="password"]', timeout=10000)
                        await google_popup.fill('input[type="password"]', password)
                        logger.debug("Google password entered.")
                        await google_popup.click('#passwordNext, button:has-text("Next")')
                        logger.debug("Clicked Google password Next button.")
                    except Exception as e:
                        logger.debug(f"Google password step failed: {e}")

                    # Wait for popup to close (OAuth redirect back to Upwork)
                    try:
                        await google_popup.wait_for_event('close', timeout=20000)
                        logger.debug("Google OAuth popup closed. Login likely succeeded.")
                    except Exception:
                        logger.debug("Popup did not close automatically. Checking main page...")

                    await asyncio.sleep(random.uniform(3.0, 5.0))
                    logger.debug("Google OAuth login flow complete.")
                    # Handle security question if it appears after OAuth
                    await handle_security_question(page)
                    body_text = await page.locator('body').inner_text()
                    logger.debug(f"Login process complete.")
                    logger.debug(f"Body text: {body_text[:500]}")
                    return True

                except Exception as e:
                    logger.debug(f"Google OAuth popup flow failed: {e}. Falling back to 'Log in a different way'...")
                    try:
                        diff_way_link = page.locator('text="Log in a different way"')
                        if await diff_way_link.count() > 0 and await diff_way_link.is_visible(timeout=3000):
                            await diff_way_link.click()
                            await asyncio.sleep(random.uniform(1.5, 2.5))
                            logger.debug("Clicked 'Log in a different way' as fallback.")
                    except Exception as e2:
                        logger.debug(f"Fallback 'Log in a different way' also failed: {e2}")

            # --- Password Step (for non-Google SSO or fallback) ---
            await page.wait_for_selector('#login_password', timeout=10000)
            await human_type(page, '#login_password', password)
            logger.debug(f"Password entered.")
            
            # Button Click Strategy (Password)
            try:
                # Attempt to click "Log In" button
                login_btn = page.locator('#login_control_continue')
                await login_btn.click(timeout=6000)
                logger.debug("Clicked 'Log In' button.")
            except Exception as e:
                logger.debug(f"Log In button click failed ({e}). Fallback to Enter.")
                await page.press('#login_password', 'Enter')

            await asyncio.sleep(random.uniform(3.5, 6.0))
            # Handle security question if it appears after password login
            await handle_security_question(page)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            body_text = await page.locator('body').inner_text()
            # error_texts = ['Verification failed. Please try again.', 'Please fix the errors below', 'Due to technical difficulties we are unable to process your request.']
            if 'Verification failed. Please try again.' in body_text[:500] or 'Please fix the errors below' in body_text[:500] or "Due to technical difficulties we are unable to process your request." in body_text[:500]:
                logger.debug(f"Verification on login failed. Attempt {attempt}/{max_attempts}")
                
                # --- In-place Retry Logic ---
                # Strategy 1: Click the button again
                logger.debug("Attempting in-place retry: clicking login button...")
                try:
                    login_btn = page.locator('#login_control_continue')
                    await login_btn.click(timeout=4000)
                    await asyncio.sleep(random.uniform(3.5, 6.0))
                    body_text = await page.locator('body').inner_text()
                    if not ('Verification failed. Please try again.' in body_text[:500] or 'Please fix the errors below' in body_text[:500] or "Due to technical difficulties we are unable to process your request." in body_text[:500]):
                         logger.info("✅ In-place retry (Click) succeeded (error cleared).")
                         logger.debug(f"Login process complete.")
                         logger.debug(f"Body text: {body_text[:500]}")
                         return True
                except Exception as e:
                    logger.debug(f"In-place retry (Click) failed: {e}")

                # Strategy 2: Press Enter
                logger.debug("Attempting in-place retry: pressing Enter...")
                try:
                    await page.press('#login_password', 'Enter')
                    await asyncio.sleep(random.uniform(3.5, 6.0))
                    body_text = await page.locator('body').inner_text()
                    if not ('Verification failed. Please try again.' in body_text[:500] or 'Please fix the errors below' in body_text[:500] or "Due to technical difficulties we are unable to process your request." in body_text[:500]):
                         logger.info("✅ In-place retry (Enter) succeeded (error cleared).")
                         logger.debug(f"Login process complete.")
                         logger.debug(f"Body text: {body_text[:500]}")
                         return True
                except Exception as e:
                    logger.debug(f"In-place retry (Enter) failed: {e}")
                
                # If retries fail, fall back to original logic (page reload)
                logger.debug("In-place retries failed. Proceeding with page reload/new page.")

                # Try reloading or creating a new page, but do NOT clear cookies yet
                if attempt == max_attempts // 2:
                    logger.debug("Creating a new page due to repeated login failures.")
                    page = await context.new_page()
                continue
            logger.debug(f"Login process complete.")
            logger.debug(f"Body text: {body_text[:500]}")
            return True
        except Exception as e:
            logger.debug(f"Login attempt {attempt} failed: {e}")
            await asyncio.sleep(random.uniform(3.5, 6.0))
    logger.error("⚠️ All login attempts failed.")
    return False

async def login_and_solve(
    page: Page,
    context: BrowserContext,
    username: str,
    password: str,
    search_url: str,
    login_url: str,
    credentials_provided: bool
) -> tuple[Page, BrowserContext]:
    """
    Navigate to Upwork, solve captcha if present, and log in if credentials are provided.
    """
    # go to search url
    await safe_goto(page, search_url, context)
    # bypass captcha
    logger.debug(f"Checking for captcha challenge...")
    captcha_solved = await solve_captcha(queryable=page, browser_context=context, captcha_type='cloudflare', challenge_type='interstitial', solve_attempts = 5, solve_click_delay = 6, wait_checkbox_attempts = 5, wait_checkbox_delay = 5, checkbox_click_attempts = 3, attempt_delay = 5)
    if captcha_solved:
        logger.debug(f"Successfully solved captcha challenge!")
    else:
        logger.warning(f"⚠️ No captcha challenge detected or failed to solve captcha.")
    # if credentials are provided, login
    if credentials_provided:
        logger.debug(f"Logging in...")
        
        # Human-like behavior: Try to find and click the "Log in" button on the search page first
        clicked_login_button = False
        try:
            logger.debug("Attempting to find 'Log in' button on search page...")
            # Try selectors: data-test="UpLink" (from user) or generic .login-link
            login_btn = page.locator('a[data-test="UpLink"], a.login-link').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                logger.debug("Found 'Log in' button. Clicking...")
                await login_btn.click()
                clicked_login_button = True
                # Wait for navigation or username field
                try:
                    await page.wait_for_selector('#login_username', timeout=10000)
                    logger.debug("Navigation to login page successful via click.")
                except:
                    logger.debug("Wait for #login_username timed out after click. Proceeding anyway...")
            else:
                logger.debug("'Log in' button not found or not visible.")
        except Exception as e:
            logger.debug(f"Failed to click 'Log in' button: {e}. Fallback to direct navigation.")
        
        # If we successfully clicked the button, we skip the initial goto in login_process
        login_success = await login_process(login_url, page, context, username, password, initial_navigation=not clicked_login_button)
        # if login fails, try clearing cookies and re-solving captcha
        if not login_success:
            logger.error("⚠️ Login failed after all attempts.")
            logger.info("🔴 Attempting last resort: clear cookies, re-solve captcha, and retry login...")
            try:
                await context.clear_cookies()
                page = await context.new_page()
                await safe_goto(page, search_url, context)
                # Re-solve captcha
                captcha_solved = await solve_captcha(queryable=page, browser_context=context, captcha_type='cloudflare', challenge_type='interstitial', solve_attempts = 5, solve_click_delay = 6, wait_checkbox_attempts = 5, wait_checkbox_delay = 5, checkbox_click_attempts = 3, attempt_delay = 5)
                if captcha_solved:
                    logger.info("✅ Captcha solved after clearing cookies. Retrying login...")
                else:
                    logger.warning("⚠️ Captcha could not be solved after clearing cookies.")
                # Retry login
                login_success = await login_process(login_url, page, context, username, password)
                if not login_success:
                    logger.error("⚠️Login still failed after last resort attempt (clear cookies, re-solve captcha, retry login). Aborting.")
                    # print body text
                    body_text = await page.locator('body').inner_text()
                    logger.debug(f"Body text: {body_text}")
                    raise Exception("Login failed after last resort attempt.")
                else:
                    logger.info("✅ Login succeeded after last resort attempt.")
                    # return page and context so that new context is used for scraping
                    return page, context
            except Exception as e:
                logger.error(f"⚠️ Exception during last resort login attempt: {e}")
    return page, context

def playwright_cookies_to_requests(cookies):
    """
    Convert Playwright cookies to a RequestsCookieJar.
    """
    jar = requests.cookies.RequestsCookieJar()
    for cookie in cookies:
        jar.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
    return jar

def _build_proxy_url_from_details(proxy_details: dict | None) -> str | None:
    """
    Build a proxy URL suitable for requests from a `proxy_details` dict.
    """
    if not proxy_details:
        return None
    server = proxy_details.get('server')
    if not server:
        return None
    # Ensure scheme present for parsing
    if not server.startswith(('http://', 'https://')):
        server = f"http://{server}"
    parsed = urlparse(server)
    # If credentials already embedded, keep as-is
    if parsed.username or '@' in server:
        return urlunparse(parsed)
    username = proxy_details.get('username')
    password = proxy_details.get('password')
    if not (username and password):
        return urlunparse(parsed)
    # Inject credentials
    netloc = parsed.netloc
    # If netloc contains host:port, prepend credentials
    netloc_with_auth = f"{username}:{password}@{netloc}"
    parsed_with_auth = parsed._replace(netloc=netloc_with_auth)
    return urlunparse(parsed_with_auth)

async def get_requests_session_from_playwright(context, page, max_retries=3, retry_delay=1, proxy_details: dict | None = None):
    """
    Extract cookies and user-agent from Playwright context and page, and build a requests.Session.
    """
    cookies = await context.cookies()
    user_agent = None
    for attempt in range(1, max_retries + 1):
        try:
            user_agent = await page.evaluate("() => navigator.userAgent")
            break
        except Exception as e:
            if "Execution context was destroyed" in str(e):
                logger.warning(f"Attempt {attempt}: Execution context destroyed while getting user-agent. Retrying...")
                await asyncio.sleep(retry_delay)
                if attempt == max_retries:
                    logger.error("Failed to get user-agent after multiple retries due to navigation/context loss. Using fallback user-agent.")
                    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            else:
                logger.error(f"Unexpected error while getting user-agent: {e}. Using fallback user-agent.")
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
                break
    if not user_agent:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    session = requests.Session()
    session.cookies = playwright_cookies_to_requests(cookies)
    session.headers.update({'User-Agent': user_agent})
    # Apply proxy to requests session if provided
    proxy_url = _build_proxy_url_from_details(proxy_details)
    if proxy_url:
        session.proxies.update({
            'http': proxy_url,
            'https': proxy_url,
        })
        logger.debug(f"session.proxies updated to: {proxy_url}")
    return session

async def get_job_urls_camoufox(page: Page, context: BrowserContext, search_urls: list, search_queries: list, limit: int = 50) -> dict:
    """
    Use the already-logged-in Camoufox browser page to navigate to job search
    pages and extract job URLs. Avoids switching to plain requests (which gets
    blocked by Cloudflare).
    """
    import re as _re
    search_results = {}
    pages_needed = (limit + 49) // 50
    jobs_from_last_page = limit % 50 or 50

    for query, base_url in zip(search_queries, search_urls):
        all_hrefs = []
        for page_num in range(1, pages_needed + 1):
            url = f"{base_url}&page={page_num}" if page_num > 1 else base_url
            logger.debug(f"[browser] Fetching search page {page_num}: {url}")
            try:
                await asyncio.sleep(random.uniform(2.0, 4.5))
                page = await safe_goto(page, url, context, timeout=30000)
                await asyncio.sleep(random.uniform(3.0, 6.0))

                # Extract page HTML from the browser
                html = await page.content()

                # Parse job hrefs from HTML (reuse same pattern as requests flow)
                hrefs = _re.findall(r'href="(/jobs/[^"]+~[0-9a-zA-Z]+[^"]*)"', html)
                # Deduplicate while preserving order
                seen = set()
                unique_hrefs = []
                for h in hrefs:
                    clean = h.split('?')[0]
                    if clean not in seen:
                        seen.add(clean)
                        unique_hrefs.append(f"https://www.upwork.com{clean}")

                logger.debug(f"[browser] Found {len(unique_hrefs)} jobs on page {page_num} for query '{query}'")

                if not unique_hrefs:
                    if page_num == 1:
                        body_text = await page.locator('body').inner_text()
                        logger.error(f"[browser] No jobs on page 1. Body snippet: {body_text[:300]}")
                    break

                all_hrefs.extend(unique_hrefs)
                if len(all_hrefs) >= limit:
                    all_hrefs = all_hrefs[:limit]
                    break

                if page_num == pages_needed:
                    all_hrefs = all_hrefs[:jobs_from_last_page]

            except Exception as e:
                logger.error(f"[browser] Error fetching page {page_num}: {e}")
                break

        search_results[query] = all_hrefs
    logger.debug(f"[browser] Search results: { {k: len(v) for k, v in search_results.items()} }")
    return search_results


async def camoufox_login_flow(username, password, login_url, search_url, credentials_provided, proxy_details=None, headless=False, search_urls=None, search_queries=None, limit=50) -> tuple:
    """
    Executes the Camoufox login flow.
    Returns a tuple: (job_urls_dict, requests_session)
    - job_urls_dict: dict of {query: [urls]} fetched via the browser (avoids Cloudflare blocking)
    - requests_session: requests.Session with cookies for fetching job details
    """
    # Browser Login
    async with AsyncCamoufox(headless=headless, geoip=True, humanize=True, i_know_what_im_doing=True, config={'forceScopeAccess': True}, disable_coop=True, proxy=proxy_details) as browser:
        logger.info(f"🌐 Creating browser/context/page for login (Camoufox) [Headless={headless}]...")
        try:
            context = await browser.new_context()
            page = await context.new_page()
        except Exception as e:
            logger.error(f"⚠️ Error creating browser: {e}")
            raise e
        try:
            logger.info("🔒 Solving Captcha and Logging in (Camoufox)...")
            page, context = await login_and_solve(page, context, username, password, search_url, login_url, credentials_provided)
        except Exception as e:
            logger.error(f"⚠️ Error logging in: {e}")
            raise e

        # --- Fetch job URLs in the browser (avoids Cloudflare blocking plain requests) ---
        job_urls_dict = {}
        if search_urls and search_queries:
            logger.info("💼 Getting Related Jobs (Browser)...")
            job_urls_dict = await get_job_urls_camoufox(page, context, search_urls, search_queries, limit=limit)

        # Extract cookies and user-agent, build requests session for detail fetching
        session = await get_requests_session_from_playwright(context, page, proxy_details=proxy_details)
        return job_urls_dict, session

