

import logging
from src.services.query_betterment.utils import get_gemini_client, GEMINI_FLASH_LITE
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

Your job is to write a persuasive cover letter based on the client's Job Description and our relevant portfolio excerpts.

────────────────────────────────────────────────────────────────────────────
CLIENT'S JOB DESCRIPTION SUMMARY:
────────────────────────────────────────────────────────────────────────────
Project Title    : {project_title}
Industry/Domain  : {industry_domain}
Required Skills  : {required_skills}
Scope of Work    : {scope_of_work}
Client Pain Points: {pain_points}

────────────────────────────────────────────────────────────────────────────
OUR RELEVANT PAST WORK (Portfolio Excerpts from Vector DB):
────────────────────────────────────────────────────────────────────────────
{portfolio_context}

────────────────────────────────────────────────────────────────────────────
INSTRUCTIONS:
────────────────────────────────────────────────────────────────────────────
Write exactly 4 sections without any headings or section labels. Each section should be self-contained:

1. Start with a compelling opening that grabs attention. Highlight why you're excited about this specific opportunity. Reference the client's exact problem and demonstrate deep understanding. (strict 1-paragraphs)

2. Detail your proven methodology and technical expertise. Explain how you would tackle their specific requirements. Include relevant past project experience and outcomes. (2-3 paragraphs)

3. Include the following links exactly as provided below:
   • Seraphyx / AB Ark relevant AI engineering: AB Ark AI Engineers  
   • GreyMind: GreyMind official website  
   • Spot AI: Spot AI official website  
   If Qdrant data is poor, use this section to provide your manually written links as requested. (1 paragraph)

4. Ask thoughtful, strategic questions about their technical approach and project execution. Format the questions as bullet points. Include all four questions from the example:
   • Is Textract currently producing layout-preserved output, or is the existing pipeline feeding mostly raw OCR text to Claude?
   • Which document fields are business-critical enough to require deterministic validation/retry versus accepting partial extraction?
   • Do you already have a golden evaluation set and baseline for extraction accuracy, token cost, and Bedrock prompt-cache hit rate?

WRITE ONLY the content. No section headers, no extra commentary, no introductions, no conclusions. Just the raw cover letter content.
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
        project_title    = "Senior AI Engineer - Production LLM Systems",
        required_skills  = ["Python", "FastAPI", "Qdrant", "PostgreSQL", "Async", "Textract", "Claude", "Bedrock"],
        scope_of_work    = ["Build production extraction pipelines", "Develop OCR/layout processing systems", "Implement database transactions with retry mechanisms", "Design LLM integration with Claude on AWS Bedrock", "Optimize token costs and prompt caching strategies"],
        industry_domain  = "AI/Machine Learning",
        pain_points      = ["OCR/layout processing pipeline development", "Structured validation under real SaaS workloads", "Production extraction pipeline reliability"],
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
    print("\n===== GENERATED COVER LETTER CONTENT (NO HEADINGS) =====\n")
    print(result)