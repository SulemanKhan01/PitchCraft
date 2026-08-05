#!/usr/bin/env python3
"""
Integration Test for New Cover Letter Structure
Tests the 4-section cover letter generation (HOOK, APPROACH, RELEVANT LINKS, QUESTIONS)
"""

import json
import requests
import time

# Test configuration
BASE_URL = "http://localhost:8000/api/generate"
TEST_JD = """
Title: Senior AI Engineer - Production LLM Systems
Company: TechCorp Inc.

Description:
We are seeking a Senior AI Engineer to lead the development of production-grade LLM systems and retrieval-augmented generation (RAG) pipelines. The successful candidate will design and implement scalable AI infrastructure that processes large volumes of unstructured data, generates intelligent responses, and maintains high performance under real-world conditions.

Key Responsibilities:
- Design and implement production extraction pipelines for document processing
- Develop OCR/layout processing systems with structured validation
- Build database transactions with retry mechanisms and idempotency
- Implement LLM integration using Claude on AWS Bedrock
- Optimize token costs and prompt caching strategies
- Ensure system reliability under high-traffic SaaS workloads

Required Skills:
- Python programming (FastAPI, PostgreSQL, async systems)
- Document processing and OCR technologies (Textract, layout preservation)
- Database design (Postgres/Drizzle, JSONB vs normalized columns)
- LLM integration (Claude, AWS Bedrock, provider abstractions)
- Cloud infrastructure (AWS S3, Textract)
- API development and microservices

Preferred Experience:
- Building RAG systems with vector databases (Qdrant)
- Implementing schema validation (Zod/Pydantic)
- Working with async job systems and retries
- Performance optimization and cost management
- Technical team leadership

Culture:
- Strong emphasis on reliability and production readiness
- Collaborative with cross-functional teams
- Continuous learning and improvement
- Focus on real-world problem solving
"""

def test_cover_letter_structure():
    """Test the 4-section cover letter generation (no headings)"""
    print("=== Testing Cover Letter Structure (No Headings) ===")
    
    try:
        print("Sending request to generate cover letter...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/cover-letter",
            json={"jd_text": TEST_JD}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            generated_content = result.get("generated_content", "")
            num_chunks = result.get("num_chunks_used", 0)
            
            print(f"\nNumber of Chunks Used: {num_chunks}")
            print("\n" + "="*80)
            print("GENERATED COVER LETTER CONTENT (NO HEADINGS):")
            print("="*80)
            print(generated_content)
            
            # Validate content presence (no section headers)
            print("\n" + "="*80)
            print("CONTENT VALIDATION:")
            print("="*80)
            
            content_checks = {
                "Hook content": "compelling opening" in generated_content.lower() and "excited about" in generated_content.lower(),
                "Approach content": "proven methodology" in generated_content.lower() and "technical expertise" in generated_content.lower(),
                "Links section": "Seraphyx / AB Ark relevant AI engineering" in generated_content,
                "Bullet questions": "•" in generated_content and "Is Textract currently producing" in generated_content,
                "Textract mention": "Textract" in generated_content,
                "Claude mention": "Claude" in generated_content,
                "AWS Bedrock mention": "Bedrock" in generated_content,
                "Question 2": "Which document fields are business-critical" in generated_content,
                "Question 3": "Do you already have a golden evaluation set" in generated_content,
            }
            
            for check_name, passed in content_checks.items():
                status = "✅" if passed else "❌"
                print(f"{status} {check_name}")
            
            all_checks_passed = all(content_checks.values())
            if all_checks_passed:
                print(f"\n✅ ALL CONTENT VALIDATION CHECKS PASSED!")
            else:
                print(f"\n⚠️  Some content validation checks failed.")
                
            # Check if there are any section headers
            headers = ["HOOK", "APPROACH", "RELEVANT LINKS", "QUESTIONS", "1.", "2.", "3.", "4."]
            header_found = any(header in generated_content for header in headers)
            if header_found:
                print(f"\n⚠️  WARNING: Section headers found in content!")
            else:
                print(f"\n✅ No section headers detected.")
                
        else:
            print(f"Error Response:")
            print(response.json())
            return False
            
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
        
    return True

def test_pdf_generation():
    """Test PDF generation from the generated content"""
    print("\n=== Testing PDF Generation ===")
    
    try:
        # First, generate cover letter content
        print("Generating cover letter content...")
        response = requests.post(
            f"{BASE_URL}/cover-letter",
            json={"jd_text": TEST_JD}
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_content = result.get("generated_content", "")
            
            if generated_content:
                print("Generating PDF from content...")
                pdf_response = requests.post(
                    f"{BASE_URL}/cover-letter/pdf",
                    json={"text": generated_content}
                )
                
                print(f"PDF Response Status: {pdf_response.status_code}")
                
                if pdf_response.status_code == 200:
                    filename = "test_cover_letter.pdf"
                    with open(filename, "wb") as f:
                        f.write(pdf_response.content)
                    print(f"✅ PDF generated successfully: {filename}")
                    return True
                else:
                    print(f"❌ PDF generation failed: {pdf_response.text}")
                    return False
            else:
                print("❌ No content generated for PDF test")
                return False
                
    except Exception as e:
        print(f"PDF generation test failed: {e}")
        return False

def test_docx_generation():
    """Test DOCX generation from the generated content"""
    print("\n=== Testing DOCX Generation ===")

    try:
        # First, generate cover letter content
        print("Generating cover letter content...")
        response = requests.post(
            f"{BASE_URL}/cover-letter",
            json={"jd_text": TEST_JD}
        )

        if response.status_code == 200:
            result = response.json()
            generated_content = result.get("generated_content", "")

            if generated_content:
                print("Generating DOCX from content...")
                docx_response = requests.post(
                    f"{BASE_URL}/cover-letter/docx",
                    json={"text": generated_content}
                )

                print(f"DOCX Response Status: {docx_response.status_code}")

                if docx_response.status_code == 200:
                    filename = "test_cover_letter.docx"
                    with open(filename, "wb") as f:
                        f.write(docx_response.content)
                    print(f"✅ DOCX generated successfully: {filename}")
                    return True
                else:
                    print(f"❌ DOCX generation failed: {docx_response.text}")
                    return False
            else:
                print("❌ No content generated for DOCX test")
                return False

    except Exception as e:
        print(f"DOCX generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Cover Letter Integration Tests")
    print("="*80)

    # Test 1: Cover letter structure
    structure_test_passed = test_cover_letter_structure()

    # Test 2: PDF generation
    pdf_test_passed = test_pdf_generation()

    # Test 3: DOCX generation
    docx_test_passed = test_docx_generation()

    print("\n" + "="*80)
    print("TEST SUMMARY:")
    print("="*80)
    print(f"Cover Letter Structure Test: {'✅ PASSED' if structure_test_passed else '❌ FAILED'}")
    print(f"PDF Generation Test: {'✅ PASSED' if pdf_test_passed else '❌ FAILED'}")
    print(f"DOCX Generation Test: {'✅ PASSED' if docx_test_passed else '❌ FAILED'}")

    if structure_test_passed and pdf_test_passed and docx_test_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())