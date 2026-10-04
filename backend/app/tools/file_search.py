import os
import re
from typing import Dict, Any, List
from pathlib import Path
from ..config import settings

def search_company_files(query: str = "") -> Dict[str, Any]:
    """
    Search simulated company file repository for invoice documents matching a company name or query.
    Returns structured list of matching documents with evidence paths.
    """
    invoices_dir = Path(settings.INVOICES_DIR)
    if not invoices_dir.exists():
        return {
            "success": False,
            "tool": "search_company_files",
            "error": f"Directory not found: {invoices_dir}",
            "data": {"files": []},
            "evidence": None
        }

    all_files = [f for f in os.listdir(invoices_dir) if f.lower().endswith(".pdf")]
    
    clean_query = query.lower().strip()
    stopwords = {"corp", "corporation", "inc", "ltd", "solutions", "systems", "global", "technologies", "invoice", "the", "from", "for"}
    query_tokens = [w for w in re.findall(r'[a-z0-9]+', clean_query) if w not in stopwords and len(w) >= 3]
    if not query_tokens:
        query_tokens = [w for w in re.findall(r'[a-z0-9]+', clean_query) if len(w) >= 3]

    matching_files: List[Dict[str, Any]] = []
    for filename in all_files:
        filepath = invoices_dir / filename
        stat = filepath.stat()
        file_info = {
            "filename": filename,
            "path": str(filepath),
            "size_bytes": stat.st_size,
            "modified_time": stat.st_mtime
        }
        
        normalized_fn = filename.lower()
        if not clean_query or any(token in normalized_fn for token in query_tokens) or clean_query in normalized_fn:
            matching_files.append(file_info)
        elif "invoice" in clean_query and any(term in normalized_fn for term in ["inv", "acme", "techcorp", "enterprise", "globex"]):
            matching_files.append(file_info)

    # Sort matching files so newer/latest appear last or first
    matching_files.sort(key=lambda x: x["filename"], reverse=True)

    return {
        "success": True,
        "tool": "search_company_files",
        "query": query,
        "data": {
            "total_found": len(matching_files),
            "files": [f["filename"] for f in matching_files],
            "file_details": matching_files
        },
        "evidence": [f["filename"] for f in matching_files]
    }
