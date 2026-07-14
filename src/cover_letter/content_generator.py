

import logging
from src.query_betterment.utils import get_gemini_client, GEMINI_FLASH_LITE
from .models import JDParsedResult

logger = logging.getLogger("cover_letter.content_generator")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [ContentGenerator] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False




_PROMPT_TEMPLATE = """\
You are an expert freelance proposal writer with 10+ years of experience winning clients on Upwork and similar platforms.

Your job is to write persuasive cover letter CONTENT (not a formatted letter) based on:
1. The client's Job Description (what they need)
2. Past proposal excerpts from our portfolio (proof of our experience)

The content should:
- Sound confident, specific, and human — NOT generic or robotic
- Directly address the client's pain points and required skills
- Reference similar past work as proof (use the portfolio excerpts as evidence)
- NOT use filler phrases like "I hope this message finds you well" or "I am writing to express my interest"
- NOT make up any experience — only use what is in the portfolio excerpts

─────────────────────────────────────────────────────────────────────────────
CLIENT'S JOB DESCRIPTION SUMMARY:
─────────────────────────────────────────────────────────────────────────────
Project Title    : {project_title}
Industry/Domain  : {industry_domain}
Required Skills  : {required_skills}
Scope of Work    : {scope_of_work}
Client Pain Points: {pain_points}

─────────────────────────────────────────────────────────────────────────────
OUR RELEVANT PAST WORK (Portfolio Excerpts from Vector DB):
─────────────────────────────────────────────────────────────────────────────
{portfolio_context}

─────────────────────────────────────────────────────────────────────────────
INSTRUCTIONS:
─────────────────────────────────────────────────────────────────────────────
Write 5–6 paragraphs of raw cover letter content:
1. Opening paragraph  — Hook the client. Show we understand their exact problem.
2. Middle paragraphs  — Show proof. Connect our past experience (from portfolio excerpts above) to their needs.
3. Closing paragraph  — Strong call to action. Invite them to a call or next step.

Write ONLY the paragraphs. No subject line, no greeting, no sign-off. Just the body content.
"""



def generate_content(parsed_jd:JDParsedResult , chunks):

    if chunks:
        portfolio_content = "\n\n".join([f"[From: {c.get('document_name', 'Unknown')}]\n{c.get('text', '')}"
        for c in chunks])

    else:
        portfolio_content = "No relevant past proposals found. Write based on general best practices only."

    prompt = _PROMPT_TEMPLATE.format(
        project_title    = parsed_jd.project_title or "Not specified",
        industry_domain  = parsed_jd.industry_domain or "Not specified",
        required_skills  = ", ".join(parsed_jd.required_skills) if parsed_jd.required_skills else "Not specified",
        scope_of_work    = ", ".join(parsed_jd.scope_of_work) if parsed_jd.scope_of_work else "Not specified",
        pain_points      = ", ".join(parsed_jd.pain_points) if parsed_jd.pain_points else "Not specified",
        portfolio_context = portfolio_content,
    ) 

    try:
        logger.info("Sending prompt to Gemini to generate cover letter content...")

        client = get_gemini_client()
        
        response = client.models.generate_content(
            model = GEMINI_FLASH_LITE,
            contents = prompt,
        )

        content = response.text.strip()
        logger.info("Content generated successfully")
        return content
    except Exception as exc:
        logger.error("Content generation failed (%s: %s).", type(exc).__name__, exc)
        return "Error: Could not generate cover letter content. Please try again."



if __name__ == "__main__":
    # Fake parsed JD (simulating Step 1 output)
    test_jd = JDParsedResult(
        project_title    = "Automation Engineer (n8n/Make/Zoho)",
        required_skills  = ["n8n", "Make.com", "Zoho CRM", "REST APIs", "Brevo"],
        scope_of_work    = ["Maintain automation pipelines", "Build CRM sync", "Complete reconciliation bridges"],
        industry_domain  = "Aviation / Hospitality",
        pain_points      = ["Unfinished automation backlog", "Manual data processing", "Accounting not live yet"],
        confidence       = 0.95,
    )
    # Fake chunks (simulating Step 2 output — in real use, these come from Qdrant)
    test_chunks = [
        {
            "text": "We built a full n8n automation pipeline for a logistics company that synced orders from Shopify to their CRM in real-time, reducing manual data entry by 80%.",
            "document_name": "logistics_proposal.pdf",
            "score": 0.91,
        },
        {
            "text": "Our team integrated Zoho CRM with a custom REST API, automating lead creation and follow-up sequences for a B2B SaaS company.",
            "document_name": "saas_proposal.pdf",
            "score": 0.87,
        },
    ]
    result = generate_content(test_jd, test_chunks)
    print("\n===== GENERATED CONTENT =====\n")
    print(result)