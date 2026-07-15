import logging
from src.services.query_betterment.utils import (
    get_gemini_client, 
    timer,
    parse_json_from_llm, 
    GEMINI_FLASH_LITE
)
from .models import JDParsedResult


logger = logging.getLogger("cover_letter.jd_parser")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [CL:JDParser] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False


class JDParser:

    STAGE_NAME: str = "jd_parser"

    PROMPT_TEMPLATE: str = """\
You are an expert Job Description parser for a proposal-based RAG retrieval system.

Extract the following structured information from the job description below.
Use empty lists [] or empty strings "" for fields with no matches.

Fields to extract:
project_title   — The job title, role name, or project name (e.g. "Senior React Developer", "Cloud Migration Project")
required_skills — ALL technologies, tools, frameworks, programming languages, and platforms mentioned (e.g. "React", "Node.js", "AWS", "PostgreSQL", "Docker")
scope_of_work   — Specific tasks, deliverables, responsibilities, or outcomes expected (e.g. "Build a REST API", "Migrate legacy system to cloud")
industry_domain — The industry or domain this job belongs to (e.g. "healthcare", "fintech", "e-commerce", "edtech", "SaaS")
pain_points     — Problems, challenges, pain points, or inefficiencies the client wants to solve (e.g. "Slow manual data processing", "High server costs")

Rules:
1. Extract ONLY what is explicitly stated or strongly implied in the text.
2. Do NOT invent or hallucinate details.
3. Be specific — use the exact skill names as written (e.g. "React.js" not "frontend framework").
4. Return ONLY a valid JSON object — no prose, no markdown fences:
    {{
    "project_title": "",
    "required_skills": [],
    "scope_of_work": [],
    "industry_domain": "",
    "pain_points": [],
    "confidence": <0.0–1.0 float>
    }}

Job Description:
\"\"\"
{jd_text}
\"\"\"

JSON Response:"""

    def parse(self, jd_text: str) -> JDParsedResult:
        if not jd_text or not jd_text.strip():
            logger.warning("Empty JD text received; returning empty result.")
            return JDParsedResult(
                project_title="",
                required_skills=[],
                scope_of_work=[],
                industry_domain="",
                pain_points=[],
                confidence=0.0,
            )

        prompt = self.PROMPT_TEMPLATE.format(jd_text=jd_text.strip())

        try:
            client = get_gemini_client()

            response = client.models.generate_content(
                model=GEMINI_FLASH_LITE,
                contents=prompt   
            )

            data = parse_json_from_llm(response.text)

            if data and isinstance(data, dict):
                confidence = float(data.get("confidence", 0.85))


                project_title   = str(data.get("project_title", "")).strip()
                required_skills = self.clean_list(data.get("required_skills", []))
                scope_of_work   = self.clean_list(data.get("scope_of_work", []))
                industry_domain = str(data.get("industry_domain", "")).strip()
                pain_points     = self.clean_list(data.get("pain_points", []))

    

                return JDParsedResult(
                    project_title=project_title,
                    required_skills=required_skills,
                    scope_of_work=scope_of_work,
                    industry_domain=industry_domain,
                    pain_points=pain_points,
                    confidence=confidence,
                )

        except Exception as exc:
            logger.warning("JD parsing failed (%s: %s); returning fallback.", type(exc).__name__, exc)




        return JDParsedResult(
            project_title="",
            required_skills=[],
            scope_of_work=[],
            industry_domain="",
            pain_points=[],
            confidence=0.5,
        )

    def clean_list(self, data: list) -> list[str]:
        if not isinstance(data, list):
            return []
        
        cleaned_list = []
        for item in data:
            if item:
                stripped_item = str(item).strip()
                if stripped_item:
                    cleaned_list.append(stripped_item)

        return cleaned_list


if __name__ == "__main__":

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

    parser = JDParser()

    result = parser.parse(jd_text)

    print(result)