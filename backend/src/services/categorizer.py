import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = GEMINI_API_KEY)

history_file = "data/processed/tagged_proposals.json"


def load_history() -> dict:
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_history(history_data: dict):
    os.makedirs(os.path.dirname(history_file), exist_ok = True)
    with open(history_file , "w") as f:
        json.dump(history_data , f , indent = 4)


def categorize_proposal(pdf_name: str , text: str):
    history = load_history()

    if pdf_name in history:
        print(f"[{pdf_name}] Found existing category in history: {history[pdf_name]}")
        return history[pdf_name]


    existing_categories = list(set(history.values()))

    text_preview  = text[:4000]


    prompt = f"""
    You are an expert proposal categorizer. 
    Your job is to read the proposal text and assign it to a category.
    Already existing categories: {existing_categories}
    Rules:
    1. If the proposal fits into one of the 'Already existing categories' listed above, you MUST reuse it.
    2. If it does not fit any existing category, create a brand new category (e.g. 1-2 words, like 'AI/ML', 'Web Dev', 'Mobile App', 'Cloud Migration').
    3. Respond with ONLY the category name. Do not include any explanations, formatting, or punctuation.
    Proposal Text:
    \"\"\"
    {text_preview}
    \"\"\"


    Category:"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )
    category = response.text.strip()

    history[pdf_name] = category
    save_history(history)

    print(f"[{pdf_name}] Assigned category: {category}")
    return category


if __name__ == "__main__":
    from src.extraction.extractor import extract_from_pdf
    
    pdf_file_path = "data/raw_pdfs/POC_Proposal.pdf"
    
    print(f"1. Reading text from: {pdf_file_path}...")
    pdf_text = extract_from_pdf(pdf_file_path)
    
    print("2. Sending text to Gemini for classification...")
    category = categorize_proposal("POC_Proposal.pdf", pdf_text)
    
    print("\n--- TEST SUCCESSFUL ---")
    print(f"File Name: POC_Proposal.pdf")
    print(f"Assigned Category: {category}")


