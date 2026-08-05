import requests
import json

test_jd = """
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

try:
    response = requests.post(
        'http://localhost:8000/api/generate/cover-letter',
        json={'jd_text': test_jd},
        timeout=60
    )
    print(f'Response Status: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print('Success!')
        print(f'Number of Chunks Used: {result.get("num_chunks_used", 0)}')
        print('\n=== GENERATED CONTENT ===')
        print(result.get('generated_content', ''))
    else:
        print(f'Error: {response.status_code}')
        print(response.text)
except Exception as e:
    print(f'Error: {e}')