
from src.retrieval.retriever import retrieve_chunks
import logging
from .models import JDParsedResult


logger = logging.getLogger("cover_letter.smart_retriever")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [SmartRetriever] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
    logger.propagate = False





def retrieve_smart(parsed_jd: JDParsedResult):

    queries = []

    scope_str = " ".join(parsed_jd.scope_of_work) if parsed_jd.scope_of_work else ""
    if parsed_jd.project_title or scope_str:
        queries.append(f"{parsed_jd.project_title} {scope_str}".strip())


    if parsed_jd.required_skills:
        skills_str = ", ".join(parsed_jd.required_skills)
        queries.append(f"Experience with: {skills_str}")


    pain_points_str = " ".join(parsed_jd.pain_points) if parsed_jd.pain_points else ""
    domain_str = parsed_jd.industry_domain if parsed_jd.industry_domain else ""
    if domain_str or pain_points_str:
        queries.append(f"{domain_str} project solving: {pain_points_str}".strip())


    if not queries:
        queries.append("software development proposal client case study")

    
    # print(queries)

    all_chunks = []

    for q in queries:
        try:
            chunks = retrieve_chunks(q)
            all_chunks.extend(chunks)

        except:
            print("Failed to retreive chunks")

             
    unique_chunks = {}
    for chunk in all_chunks:
        text = chunk.get("text" , "")

        if not text:
            continue

        key = text.strip()
        if key not in unique_chunks:
              unique_chunks[key] = chunk
        
        else:
            if chunk.get("score" ,0) > unique_chunks[key].get("score" , 0):
                unique_chunks[key] = chunk
        
    sorted_chunks = sorted(unique_chunks.values(), key = lambda x:x.get("score" , 0))

    final_chunks = sorted_chunks[:8]

    logger.info(
        "Retrieved %d total raw chunks → De-duplicated to %d unique → Returning top %d",
        len(all_chunks),
        len(unique_chunks),
        len(final_chunks)
    )
    return final_chunks

        

if __name__ == "__main__":
    # A fake parsed JD to test the retrieval strategy
    test_jd = JDParsedResult(
        project_title="HIPAA-Compliant Patient Portal",
        required_skills=["React", "Node.js", "AWS", "PostgreSQL"],
        scope_of_work=["Build scheduling system", "Secure messaging feature"],
        industry_domain="Healthcare",
        pain_points=["Data security worries", "Scalability issues"],
        confidence=0.95
    )
    # Call function directly
    results = retrieve_smart(test_jd)
    print("\n===== RETRIEVED CHUNKS =====")
    for idx, c in enumerate(results, 1):
        print(f"\n[{idx}] Score: {c.get('score', 0):.4f} | Doc: {c.get('document_name')}")
        print(c.get("text")[:200] + "...")
        
        

    
