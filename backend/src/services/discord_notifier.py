import httpx
import os

from dotenv import load_dotenv

def send_job_alert(job_title, budget, url, skills):

    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    
    payload = {
        "embeds": [{
            "title": f"🎯 New Upwork Job: {job_title}",
            "url": url,
            "color": 5814783, # Purple accent
            "fields": [
                {"name": "Budget / Rate", "value": str(budget), "inline": True},
                {"name": "Skills", "value": str(skills), "inline": True}
            ],
            "footer": {"text": "PitchCraft Upwork Radar"}
        }]
    }
    try:
        httpx.post(webhook_url, json=payload, timeout=5.0)
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")
