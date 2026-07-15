import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph

def generate_minimal_pdf(cover_letter_text: str) -> bytes:
    """
    Generates a minimalist, text-only PDF in-memory.
    - Margins: 1 inch (72 points)
    - Font: 11pt Helvetica
    - Leading: 16pt (approx 1.45x line height)
    - Color: Charcoal gray (#2D3748) for a softer, premium reading experience.
    """
    buffer = io.BytesIO()
    
    # 72 points = 1 inch margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Define a clean, modern body style
    body_style = ParagraphStyle(
        'MinimalBodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16, 
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=14  # Space between paragraphs
    )
    
    # Split text into clean paragraphs
    raw_paragraphs = [p.strip() for p in cover_letter_text.split('\n') if p.strip()]
    
    for p_text in raw_paragraphs:
        # Replace internal newlines with space to prevent unexpected line breaks in reportlab Paragraphs
        cleaned_text = p_text.replace('\n', ' ')
        story.append(Paragraph(cleaned_text, body_style))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
