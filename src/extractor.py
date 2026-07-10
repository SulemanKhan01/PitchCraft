import pdfplumber

def extract_from_pdf(pdf_path: str):
    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text.append(page_text)

    return("\n".join(all_text).strip())
        

if __name__ == "__main__":
    text = extract_from_pdf(r"C:\Users\PC\Documents\ab_ark\PitchCraft\data\raw_pdfs\POC_Proposal.pdf")
    print(text)