"""
generator.py — OpenAI static website code generation service using Structured Output.
"""
import json
from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.services.website_generator.validator import validate_generated_website

SYSTEM_PROMPT = """You are a World-Class Frontend Developer and UI/UX Designer.
Your task is to generate a modern, responsive, visually stunning single-page static website based on the user's prompt.

You MUST return a single valid JSON object with exact keys:
1. "site_title": Short descriptive title for the website
2. "index_html": Complete semantic HTML5 code. Must include hero section, features/about, testimonials/gallery, contact section, and footer.
3. "styles_css": Modern Vanilla CSS code using custom properties (CSS variables), modern Google typography (@import url('https://fonts.googleapis.com/...')), sleek dark mode / subtle gradients, flexbox/grid, and smooth hover animations. Do NOT use external CSS frameworks like Tailwind or Bootstrap; use rich custom CSS!
4. "script_js": Vanilla JavaScript code for interactive UI elements (e.g. mobile navigation toggle, smooth scroll for nav links, modal dialogs, form submit feedback).

Rules:
- Do NOT wrap code inside markdown fences in the JSON strings.
- Ensure all interactive buttons, links, and forms function gracefully in frontend.
- Do NOT require external backend APIs or backend databases.
"""

def generate_website_code(prompt: str) -> dict:
    """
    Calls OpenAI API to generate website HTML, CSS, and JS.
    Returns validated dictionary of static files: {"index.html": ..., "styles.css": ..., "script.js": ...}
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in backend environment variables.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    user_message = f"User Request: {prompt}\n\nPlease generate complete code for index.html, styles.css, and script.js."

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=4000
    )

    raw_content = response.choices[0].message.content
    
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as err:
        raise ValueError(f"Failed to parse AI output as JSON: {err}")

    # Validate and clean files
    validated_files = validate_generated_website(data)
    validated_files["site_title"] = data.get("site_title", "AI Generated Website")

    return validated_files
