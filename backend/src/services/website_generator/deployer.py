"""
deployer.py — In-memory ZIP packager and Netlify API deployment service.
"""
import io
import zipfile
import requests
from src.config import NETLIFY_AUTH_TOKEN

NETLIFY_SITES_API = "https://api.netlify.com/api/v1/sites"

def create_in_memory_zip(files: dict) -> bytes:
    """
    Compresses static website files (index.html, styles.css, script.js) into an in-memory ZIP archive.
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in ["index.html", "styles.css", "script.js"]:
            content = files.get(filename, "")
            zf.writestr(filename, content.encode("utf-8"))
            
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def deploy_to_netlify(files: dict) -> dict:
    """
    Deploys static files directly to Netlify via API ZIP upload.
    Returns dictionary with public_url and site_id.
    """
    if not NETLIFY_AUTH_TOKEN:
        raise ValueError("NETLIFY_AUTH_TOKEN is missing. Please set it in backend/.env.")

    # 1. Build in-memory zip binary
    zip_bytes = create_in_memory_zip(files)

    headers = {
        "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
        "Content-Type": "application/zip"
    }

    # 2. Upload zip to Netlify sites endpoint (creates site & deploys instantly)
    response = requests.post(NETLIFY_SITES_API, data=zip_bytes, headers=headers, timeout=30)

    if response.status_code not in (200, 201):
        err_msg = response.text
        try:
            err_json = response.json()
            err_msg = err_json.get("message", response.text)
        except Exception:
            pass
        raise RuntimeError(f"Netlify deployment failed (HTTP {response.status_code}): {err_msg}")

    result = response.json()
    
    public_url = result.get("ssl_url") or result.get("url")
    site_id = result.get("id") or result.get("site_id")

    if not public_url:
        raise RuntimeError("Netlify deployment completed but no public URL was returned.")

    return {
        "public_url": public_url,
        "site_id": site_id,
        "site_name": result.get("name")
    }
