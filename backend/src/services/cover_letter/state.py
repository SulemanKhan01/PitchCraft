from typing import TypedDict, Optional, List, Dict, Any
from .models import JDParsedResult


class CoverLetterState(TypedDict):
    
    jd_text :str
    parsed_jd :Optional[JDParsedResult]
    chunks           : Optional[List[Dict[str, Any]]]
    generated_content: Optional[str]               
    error            : Optional[str] 