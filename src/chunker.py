import re
import logging

# --- LOGGING CONFIGURATION ---
# Set ENABLE_LOGGING to True to show detailed chunker logs during testing.
# Set it to False to completely disable logging.
ENABLE_LOGGING = True

logger = logging.getLogger("chunker")
# Prevent duplicate log configurations
if not logger.handlers:
    logger.setLevel(logging.DEBUG if ENABLE_LOGGING else logging.CRITICAL)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[Chunker] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False


class RecursiveCharacterTextSplitter:
    """
    A recursive character text splitter that splits text by trying a sequence of separators.
    Falls back to fixed-length chunking if no separator works or if separators are exhausted.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: list = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> list[str]:
        logger.debug(f"Splitting text of length {len(text)} using RecursiveCharacterTextSplitter")
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: list) -> list[str]:
        if len(text) <= self.chunk_size:
            logger.debug(f"  Chunk size {len(text)} <= {self.chunk_size}, keeping intact.")
            return [text]
        
        if not separators:
            logger.debug(f"  No separators left. Falling back to fixed-length split for remaining {len(text)} chars.")
            # Fall back to fixed-length splitting if no separators are left
            return self._fixed_length_split(text, self.chunk_size, self.chunk_overlap)
        
        separator = separators[0]
        next_separators = separators[1:]
        
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)
        
        chunks = []
        current_doc = []
        current_len = 0
        
        for split in splits:
            if len(split) > self.chunk_size:
                # Flush the current chunk before handling the oversized split
                if current_doc:
                    chunks.append(separator.join(current_doc))
                    current_doc = []
                    current_len = 0
                
                # Recursively split the oversized part
                recursive_splits = self._split_text(split, next_separators)
                chunks.extend(recursive_splits)
                continue
            
            # Calculate length with separator if it's not the first element in the current chunk
            add_len = len(split) + (len(separator) if current_doc else 0)
            
            if current_len + add_len <= self.chunk_size:
                current_doc.append(split)
                current_len += add_len
            else:
                if current_doc:
                    chunks.append(separator.join(current_doc))
                
                # Overlap calculation: back-track and keep elements from the end
                # of current_doc up to chunk_overlap size
                overlap_doc = []
                overlap_len = 0
                for item in reversed(current_doc):
                    item_add_len = len(item) + (len(separator) if overlap_doc else 0)
                    if overlap_len + item_add_len <= self.chunk_overlap:
                        overlap_doc.insert(0, item)
                        overlap_len += item_add_len
                    else:
                        break
                
                current_doc = overlap_doc.copy()
                current_len = overlap_len
                
                # Add the current split
                add_len = len(split) + (len(separator) if current_doc else 0)
                current_doc.append(split)
                current_len += add_len
        
        if current_doc:
            chunks.append(separator.join(current_doc))
            
        return chunks

    def _fixed_length_split(self, text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        logger.debug(f"    Performing fixed length split on {len(text)} chars (chunk_size: {chunk_size}, overlap: {chunk_overlap})")
        if chunk_size <= 0:
            return [text]
        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size - 1
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - chunk_overlap)
            if start >= len(text):
                break
        return chunks


def fixed_length_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Slices text into fixed-length segments of chunk_size with chunk_overlap.
    """
    if chunk_size <= 0:
        return [text]
    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size - 1
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - chunk_overlap)
        if start >= len(text):
            break
    return chunks


def detect_sections(text: str) -> list[dict]:
    """
    Splits the document text into sections based on headings.
    Returns a list of dicts: [{'title': str, 'content': str}]
    """
    logger.debug(f"Detecting sections in text (length: {len(text)})...")
    lines = text.split('\n')
    
    # Heading patterns:
    # 1. Ends with a colon (e.g. "Project Overview:", "Tech Stack:")
    # 2. Starts with specific keywords (e.g. "Proposal Document", "Timeline")
    # 3. Line is relatively short (<= 80 chars)
    # 4. Line is not a list item or bullet point
    HEADING_PATTERNS = [
        r'^.+:\s*$',  # Ends with a colon
        r'^(?:Proposal Document|Timeline)\b.*$',  # Starts with specific keywords
    ]
    
    def is_heading(line: str) -> bool:
        line_stripped = line.strip()
        if not line_stripped:
            return False
        if len(line_stripped) > 80:
            return False
        if line_stripped.startswith(('●', '○', '•', '*', '-', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
            return False
        for pattern in HEADING_PATTERNS:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                return True
        return False

    sections = []
    current_title = "Introduction"
    current_content_lines = []
    first_line_seen = False
    
    for line in lines:
        if is_heading(line):
            if current_content_lines or first_line_seen:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_content_lines).strip()
                })
            current_title = line.strip()
            current_content_lines = []
            first_line_seen = True
        else:
            if line.strip() or current_content_lines:
                current_content_lines.append(line)
            if line.strip():
                first_line_seen = True

    if current_content_lines or first_line_seen:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_content_lines).strip()
        })
        
    # Clean up empty sections
    sections = [s for s in sections if s["content"].strip()]
    
    if not sections:
        sections = [{"title": "Document", "content": text.strip()}]
        
    logger.debug(f"Detected {len(sections)} sections: {', '.join([repr(s['title']) for s in sections])}")
    return sections


def chunk_document(text: str, max_chunk_size: int = 500, chunk_overlap: int = 50, metadata: dict = None) -> list[dict]:
    """
    Chunks a document according to the following strategy:
    1. Detect sections using headings.
    2. For each section:
       a. If section size <= max_chunk_size, return it as a single chunk.
       b. If section size > max_chunk_size, apply RecursiveCharacterTextSplitter.
       c. If any resulting chunk is still > max_chunk_size, apply Fixed-Length Chunking.
    3. Return final chunks with order and section title in metadata.
    """
    logger.debug(f"--- Starting Chunking (Length: {len(text)}, Max Chunk Size: {max_chunk_size}, Overlap: {chunk_overlap}) ---")
    if metadata is None:
        metadata = {}
        
    sections = detect_sections(text)
    final_chunks = []
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=max_chunk_size, chunk_overlap=chunk_overlap)
    
    for idx, section in enumerate(sections):
        section_title = section["title"]
        content = section["content"]
        
        logger.debug(f"Processing Section {idx+1}/{len(sections)}: {repr(section_title)} (Length: {len(content)})")
        
        section_chunks = []
        if len(content) <= max_chunk_size:
            logger.debug(f"  Section {repr(section_title)} fits within max_chunk_size. Kept intact.")
            section_chunks.append(content)
        else:
            logger.debug(f"  Section {repr(section_title)} exceeds max_chunk_size. Splitting...")
            recursive_chunks = splitter.split_text(content)
            
            for r_chunk in recursive_chunks:
                if len(r_chunk) > max_chunk_size:
                    logger.debug(f"    Sub-chunk of {repr(section_title)} ({len(r_chunk)} chars) still exceeds max_chunk_size. Slicing with fixed-length splitting.")
                    fixed_chunks = fixed_length_split(r_chunk, max_chunk_size, chunk_overlap)
                    section_chunks.extend(fixed_chunks)
                else:
                    section_chunks.append(r_chunk)
                    
        logger.debug(f"  Section {repr(section_title)} resulted in {len(section_chunks)} chunks.")
        # Construct output dictionary for each chunk, preserving metadata and adding section_title
        for chunk_text in section_chunks:
            chunk_metadata = metadata.copy()
            chunk_metadata["section_title"] = section_title
            
            final_chunks.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
            
    logger.debug(f"--- Chunking Completed: Generated {len(final_chunks)} chunks. ---\n")
    return final_chunks


if __name__ == "__main__":
    from extractor import extract_from_pdf
    
    pdf_file_path = "data/raw_pdfs/POC_Proposal.pdf"
    print(f"1. Reading text from: {pdf_file_path}...")
    pdf_text = extract_from_pdf(pdf_file_path)
    
    print("\n2. Running chunk_document with logging enabled:")
    sample_metadata = {"file_name": "POC_Proposal.pdf", "category": "AI/RAG"}
    chunks = chunk_document(pdf_text, metadata=sample_metadata)
    
    print(f"\n3. Total chunks created: {len(chunks)}")
    for idx, chunk in enumerate(chunks[:3]):
        # Replace non-ascii bullet points to prevent Windows encoding errors when printing preview
        section_title = chunk['metadata']['section_title'].replace('\u25cf', '-').replace('\u25cb', '-')
        preview = chunk['text'][:150].replace('\u25cf', '-').replace('\u25cb', '-')
        print(f"\n--- Sample Chunk {idx+1} (Section: {section_title}) ---")
        print(f"Metadata: {chunk['metadata']}")
        print(preview + "...")
