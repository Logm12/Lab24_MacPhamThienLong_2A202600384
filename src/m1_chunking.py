"""
Module 1: Advanced Chunking Strategies
=======================================
Implement semantic, hierarchical, và structure-aware chunking.
So sánh với basic chunking (baseline) để thấy improvement.

Test: pytest tests/test_m1.py
"""

import os, sys, glob, re
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (DATA_DIR, HIERARCHICAL_PARENT_SIZE, HIERARCHICAL_CHILD_SIZE,
                    SEMANTIC_THRESHOLD)


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)
    parent_id: str | None = None


def load_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """Load all markdown/text files from data/."""
    docs = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(fp, encoding="utf-8") as f:
            docs.append({"text": f.read(), "metadata": {"source": os.path.basename(fp)}})
    return docs


# Baseline: Basic Chunking (để so sánh)


def chunk_basic(text: str, chunk_size: int = 500, metadata: dict | None = None) -> list[Chunk]:
    """
    Basic chunking: split theo paragraph (\\n\\n).
    Đây là baseline — KHÔNG phải mục tiêu của module này.
    """
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for i, para in enumerate(paragraphs):
        if len(current) + len(para) > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
            current = ""
        current += para + "\n\n"
    if current.strip():
        chunks.append(Chunk(text=current.strip(), metadata={**metadata, "chunk_index": len(chunks)}))
    return chunks


# Strategy 1: Semantic Chunking


def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    """
    Split text by sentence similarity — nhóm câu cùng chủ đề.
    Tốt hơn basic vì không cắt giữa ý.

    Args:
        text: Input text.
        threshold: Cosine similarity threshold. Dưới threshold → tách chunk mới.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        List of Chunk objects grouped by semantic similarity.
    """
    metadata = metadata or {}
    
    # 1. Split text into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n\n', text) if s.strip()]
    if not sentences:
        return []
        
    # 2. Encode sentences
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast & small
    embeddings = model.encode(sentences)
    
    # 3. Group sentences
    chunks = []
    current_group = [sentences[0]]
    
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    for i in range(1, len(sentences)):
        sim = cosine_sim(embeddings[i-1], embeddings[i])
        if sim < threshold:
            chunks.append(Chunk(
                text=" ".join(current_group), 
                metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"}
            ))
            current_group = []
        current_group.append(sentences[i])
        
    # Don't forget last group
    if current_group:
        chunks.append(Chunk(
            text=" ".join(current_group), 
            metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"}
        ))
        
    return chunks


# Strategy 2: Hierarchical Chunking


def chunk_hierarchical(text: str, parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:
    """
    Parent-child hierarchy: retrieve child (precision) → return parent (context).
    Đây là default recommendation cho production RAG.

    Args:
        text: Input text.
        parent_size: Chars per parent chunk.
        child_size: Chars per child chunk.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        (parents, children) — mỗi child có parent_id link đến parent.
    """
    metadata = metadata or {}
    parents = []
    children = []
    
    # 1. Split text into parents (using basic paragraph-based logic but limited by parent_size)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    current_parent_text = ""
    p_index = 0
    
    for para in paragraphs:
        if len(current_parent_text) + len(para) > parent_size and current_parent_text:
            pid = f"{metadata.get('source', 'doc')}_p{p_index}"
            parent_chunk = Chunk(text=current_parent_text.strip(), metadata={**metadata, "chunk_type": "parent", "parent_id": pid})
            parents.append(parent_chunk)
            
            # 2. Split each parent into children
            # Sliding window with 50% overlap for children
            step = child_size // 2
            for c_idx, start in enumerate(range(0, len(current_parent_text), step)):
                child_text = current_parent_text[start : start + child_size].strip()
                if len(child_text) > 20: # skip tiny fragments
                    children.append(Chunk(
                        text=child_text, 
                        metadata={**metadata, "chunk_type": "child", "chunk_index": c_idx}, 
                        parent_id=pid
                    ))
            
            current_parent_text = ""
            p_index += 1
            
        current_parent_text += para + "\n\n"
        
    if current_parent_text.strip():
        pid = f"{metadata.get('source', 'doc')}_p{p_index}"
        parent_chunk = Chunk(text=current_parent_text.strip(), metadata={**metadata, "chunk_type": "parent", "parent_id": pid})
        parents.append(parent_chunk)
        
        step = child_size // 2
        for c_idx, start in enumerate(range(0, len(current_parent_text), step)):
            child_text = current_parent_text[start : start + child_size].strip()
            if len(child_text) > 20:
                children.append(Chunk(
                    text=child_text, 
                    metadata={**metadata, "chunk_type": "child", "chunk_index": c_idx}, 
                    parent_id=pid
                ))
                
    return parents, children


# Strategy 3: Structure-Aware Chunking


def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    """
    Parse markdown headers → chunk theo logical structure.
    Giữ nguyên tables, code blocks, lists — không cắt giữa chừng.

    Args:
        text: Markdown text.
        metadata: Metadata gắn vào mỗi chunk.

    Returns:
        List of Chunk objects, mỗi chunk = 1 section (header + content).
    """
    metadata = metadata or {}
    # 1. Split by markdown headers:
    sections = re.split(r'(^#{1,6}\s+.+$)', text, flags=re.MULTILINE)
    
    chunks = []
    current_header = "Intro"
    current_content = ""
    
    for part in sections:
        if not part:
            continue
        if re.match(r'^#{1,6}\s+', part):
            if current_content.strip():
                chunks.append(Chunk(
                    text=f"{current_header}\n{current_content}".strip(),
                    metadata={**metadata, "section": current_header, "strategy": "structure", "chunk_index": len(chunks)}
                ))
            current_header = part.strip()
            current_content = ""
        else:
            current_content += part
            
    # Don't forget last section
    if current_content.strip() or current_header:
        chunks.append(Chunk(
            text=f"{current_header}\n{current_content}".strip(),
            metadata={**metadata, "section": current_header, "strategy": "structure", "chunk_index": len(chunks)}
        ))
        
    return chunks


# A/B Test: Compare All Strategies


def compare_strategies(documents: list[dict]) -> dict:
    """
    Run all strategies on documents and compare.

    Returns:
        {"basic": {...}, "semantic": {...}, "hierarchical": {...}, "structure": {...}}
    """
    results = {
        "basic": {"count": 0, "len": []},
        "semantic": {"count": 0, "len": []},
        "hierarchical": {"parents": 0, "children": 0, "child_len": []},
        "structure": {"count": 0, "len": []}
    }
    
    for doc in documents:
        text = doc["text"]
        meta = doc["metadata"]
        
        # Basic
        b_chunks = chunk_basic(text, metadata=meta)
        results["basic"]["count"] += len(b_chunks)
        results["basic"]["len"].extend([len(c.text) for c in b_chunks])
        
        # Semantic
        s_chunks = chunk_semantic(text, metadata=meta)
        results["semantic"]["count"] += len(s_chunks)
        results["semantic"]["len"].extend([len(c.text) for c in s_chunks])
        
        # Hierarchical
        parents, children = chunk_hierarchical(text, metadata=meta)
        results["hierarchical"]["parents"] += len(parents)
        results["hierarchical"]["children"] += len(children)
        results["hierarchical"]["child_len"].extend([len(c.text) for c in children])
        
        # Structure
        st_chunks = chunk_structure_aware(text, metadata=meta)
        results["structure"]["count"] += len(st_chunks)
        results["structure"]["len"].extend([len(c.text) for c in st_chunks])
        
    # Summarize stats
    import numpy as np
    summary = {}
    for name, data in results.items():
        if name == "hierarchical":
            summary[name] = {
                "parents": data["parents"],
                "children": data["children"],
                "avg_child_len": int(np.mean(data["child_len"])) if data["child_len"] else 0
            }
        else:
            summary[name] = {
                "count": data["count"],
                "avg_len": int(np.mean(data["len"])) if data["len"] else 0,
                "min_len": int(np.min(data["len"])) if data["len"] else 0,
                "max_len": int(np.max(data["len"])) if data["len"] else 0
            }
            
    print("\n" + "="*60)
    print(f"{'Strategy':<15} | {'Count':<6} | {'Avg Len':<8} | {'Min':<4} | {'Max':<4}")
    print("-" * 60)
    for name, stats in summary.items():
        if name == "hierarchical":
             print(f"{name:<15} | {stats['children']:<6} | {stats['avg_child_len']:<8} | {'-':<4} | {'-':<4} (p={stats['parents']})")
        else:
             print(f"{name:<15} | {stats['count']:<6} | {stats['avg_len']:<8} | {stats['min_len']:<4} | {stats['max_len']:<4}")
    
    return summary


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    results = compare_strategies(docs)
    for name, stats in results.items():
        print(f"  {name}: {stats}")
