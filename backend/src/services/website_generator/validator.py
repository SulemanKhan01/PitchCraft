"""
validator.py — Code validation and sanitization service for generated static websites.
"""
import re

def clean_code_block(code_str: str, file_type: str = "html") -> str:
    """
    Removes markdown code fences like ```html or ```css if LLM wraps output in markdown.
    """
    if not code_str:
        return ""
    
    # Strip leading/trailing whitespaces
    code_str = code_str.strip()

    # Remove markdown code blocks if present
    pattern = rf"^```(?:{file_type}|html|css|javascript|js)?\s*\n?(.*?)\n?```$"
    match = re.search(pattern, code_str, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback strip of triple backticks
    if code_str.startswith("```") and code_str.endswith("```"):
        lines = code_str.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()

    return code_str


def validate_generated_website(files_dict: dict) -> dict:
    """
    Validates that required files are present and contain basic static HTML structure.
    Returns cleaned files dictionary.
    """
    index_html = clean_code_block(files_dict.get("index_html", ""), "html")
    styles_css = clean_code_block(files_dict.get("styles_css", ""), "css")
    script_js  = clean_code_block(files_dict.get("script_js", ""), "js")

    # 1. Ensure index.html exists and is non-empty
    if not index_html or len(index_html.strip()) < 5:
        raise ValueError("Generated HTML content is empty or invalid.")

    # 2. Check for basic HTML tags
    if "<html" not in index_html.lower() or "<body" not in index_html.lower():
        # Inject standard HTML envelope if missing
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
{index_html}
    <script src="script.js"></script>
</body>
</html>"""

    # 3. Ensure styles.css link is included in head
    if 'href="styles.css"' not in index_html and "href='styles.css'" not in index_html:
        index_html = index_html.replace("</head>", '    <link rel="stylesheet" href="styles.css">\n</head>')

    # 4. Ensure script.js script tag is included before closing body
    if 'src="script.js"' not in index_html and "src='script.js'" not in index_html:
        index_html = index_html.replace("</body>", '    <script src="script.js"></script>\n</body>')

    return {
        "index.html": index_html,
        "styles.css": styles_css,
        "script.js": script_js
    }
