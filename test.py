import requests

# The full, multi-line job description
jd_text = """
Title: Automation Engineer (n8n/Make/Zoho) — Full-Time Freelance, 3 Months, Aviation/Hospitality Business 
Category: Automation / Zapier & Make Experts (or Web Automation) 
Description: 
We're a boutique aviation catering & services company running a growing stack of business-process 
automations, and we need a hands-on automation engineer to join us full-time for an initial 3-month contract, 
with strong potential to extend. 
About the role 
You'll take ownership of an existing automation ecosystem and push forward a active backlog. We already 
have working pipelines in production (Zoho CRM/Books, n8n, Make.com, Render-hosted bridges, Apollo 
enrichment, Brevo campaigns) — you'll maintain, finish, and extend them. 
Current priorities (in order): 
Sales prospecting automations — finishing lead sourcing, enrichment, matching, and CRM sync pipelines 
(airport/contact monitoring, fuzzy-matching logic, multi-path review workflows). 
Accounting automations — completing bank/payment reconciliation bridges (Stripe → Zoho, bank → Zoho), 
moving them from test to live, and building out supplier-bill/COGS automation. 
New business unit rollout — we're launching a second, related company and will need a parallel automation 
setup (CRM, invoicing, outreach) built essentially from scratch. 
What we're looking for 
Strong hands-on experience with n8n and/or Make.com (real production builds, not just tutorials) 
Comfortable with Zoho CRM/Books (or equivalent CRM/accounting APIs) and OAuth-based integrations 
Can read/write to REST APIs, webhooks, and cron-based jobs; comfortable deploying small services on Render 
or similar 
Experience with email/CRM tools like Brevo, Apollo, or similar is a plus 
Autonomous — able to take a messy backlog and prioritize it — but communicative: we'll run daily check-ins 
(async update + short call as needed) 
Fluent in English (written and spoken) 
Logistics 
Full-time freelance commitment, 3-month initial contract 
Daily overlap with Dubai timezone required 
Access will be provided to existing repos, Render dashboards, and Zoho sandbox for a paid trial task before full 
onboarding, if needed 
To apply, please include: 
1–2 examples of automations you've built (n8n or Make.com), ideally with a Loom walkthrough 
Your experience with Zoho or similar CRM/accounting platforms 
Your availability for daily overlap and start date 
"""

url = "http://localhost:8000/api/generate/cover-letter"

print("Sending request to FastAPI...")
try:
    response = requests.post(url, json={"jd_text": jd_text})
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n===== GENERATED COVER LETTER CONTENT =====")
        print(result.get("generated_content"))
        print(f"\nNumber of Chunks Used: {result.get('num_chunks_used')}")
    else:
        print("Error Response:")
        print(response.json())
        
except Exception as e:
    print(f"Connection failed: {e}")
