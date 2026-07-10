
if __name__ == "__main__":
    from extractor import extract_from_pdf
    from categorizer import categorize_proposal
    
    pdf_file_path = "data/raw_pdfs/POC_Proposal.pdf"
    
    print(f"1. Reading text from: {pdf_file_path}...")
    pdf_text = extract_from_pdf(pdf_file_path)
    
    print("2. Sending text to Gemini for classification...")
    category = categorize_proposal("POC_Proposal.pdf", pdf_text)
    
    print("\n--- TEST SUCCESSFUL ---")
    print(f"File Name: POC_Proposal.pdf")
    print(f"Assigned Category: {category}")
