"""
SHL Assessment Recommendation Engine
Uses sentence embeddings + LLM reranking for intelligent assessment recommendations
"""

import json
import numpy as np
import os
import re
import logging
import time
from typing import List, Dict, Optional, Tuple
import requests


# Get the base directory (/app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 

# Build the path including the 'shl-recommendation' folder
catalog_path = os.path.join(BASE_DIR, "shl-recommendation", "scripts", "data", "shl_catalog.json")
embeddings_path = os.path.join(BASE_DIR, "shl-recommendation", "scripts", "data", "shl_catalog_embeddings.npy")

print(f"--- DEBUG: ACTUAL SEARCH PATH: {catalog_path} ---")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Configuration - 2026 STABLE PATHS
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # Set via: set GEMINI_API_KEY=your_key

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "\n\n  GEMINI_API_KEY is not set!\n"
        "  Run this before starting the server:\n"
        "    set GEMINI_API_KEY=AIzaSyAn0o1Wy9aRd8Pl1JNH8FCTa6fUwhj_3xo\n"
    )

# Base URLs ONLY — key passed via params={"key":...} at call time, never baked into URL string.
# text-embedding-004  → 768-dim vectors, requires v1beta
# gemini-2.0-flash-001 → stable GA model name (not the alias gemini-2.0-flash)
# 1. Use the most stable embedding model for v1beta
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"

# 2. The new stable Flash model (Replaces gemini-2.0-flash-001)
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# 3. New dimension for gemini-embedding-001 (IMPORTANT)
EXPECTED_EMBED_DIM = 768

# 3. Robust Path Logic
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_file_dir
while project_root and not os.path.exists(os.path.join(project_root, 'scripts')):
    parent = os.path.dirname(project_root)
    if parent == project_root: break
    project_root = parent

CATALOG_PATH = os.path.join(project_root, 'scripts', 'data', 'shl_catalog.json')
print(f"--- SUCCESS: ENGINE POINTED TO {CATALOG_PATH} ---")


# ---------------------------------------------------------------------------
# Embedding utilities
# ---------------------------------------------------------------------------

def get_embedding_gemini(text: str, api_key: str, max_retries: int = 5) -> Optional[np.ndarray]:
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text[:8192]}]}
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                GEMINI_EMBED_URL,
                params={"key": api_key},
                json=payload,
                timeout=30 # Increased timeout for 'Read timed out' errors
            )
            
            if resp.status_code == 429:
                # Rate limit hit: wait and retry with exponential backoff
                wait_time = (2 ** attempt) + random.random()
                logger.warning(f"Rate limit hit. Waiting {wait_time:.2f}s before retry {attempt+1}/{max_retries}")
                time.sleep(wait_time)
                continue
                
            resp.raise_for_status()
            values = resp.json()['embedding']['values']
            
            # Small mandatory pause to stay under the 15 RPM limit
            time.sleep(1.5) 
            
            return np.array(values, dtype=np.float32)

        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            wait_time = (2 ** attempt) + 2
            logger.warning(f"Network issue. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return None
            
    return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Assessment text building
# ---------------------------------------------------------------------------

def build_assessment_text(assessment: Dict) -> str:
    """Build a rich text representation of an assessment for embedding."""
    parts = []
    
    name = assessment.get('name', '')
    if name:
        parts.append(f"Assessment: {name}")
    
    desc = assessment.get('description', '')
    if desc:
        parts.append(f"Description: {desc}")
    
    test_types = assessment.get('test_type', [])
    if test_types:
        parts.append(f"Test Types: {', '.join(test_types)}")
    
    duration = assessment.get('duration')
    if duration:
        parts.append(f"Duration: {duration} minutes")
    
    adaptive = assessment.get('adaptive_support', 'No')
    remote = assessment.get('remote_support', 'Yes')
    parts.append(f"Adaptive: {adaptive}. Remote: {remote}.")
    
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Catalog manager
# ---------------------------------------------------------------------------

class CatalogManager:
    """Manages the SHL assessment catalog with embeddings."""
    
    def __init__(self, catalog_path: str = CATALOG_PATH, api_key: str = ""):
        self.catalog_path = catalog_path
        self.api_key = api_key or GEMINI_API_KEY
        self.assessments: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.embeddings_path = catalog_path.replace('.json', '_embeddings.npy')
        
    def load_catalog(self):
        """Load catalog from JSON file."""
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            self.assessments = json.load(f)
        logger.info(f"Loaded {len(self.assessments)} assessments from catalog")
    
    def build_embeddings(self, force_rebuild: bool = False):
        """Build or load embeddings for all assessments."""
        if not force_rebuild and os.path.exists(self.embeddings_path):
            cached = np.load(self.embeddings_path)
            # Validate dimension matches current model (text-embedding-004 = 768 dims)
            # Old cache may be 3072-dim from a different model — delete and rebuild
            if cached.shape[1] != EXPECTED_EMBED_DIM:
                logger.warning(
                    f"Cached embeddings have {cached.shape[1]} dims but model needs "
                    f"{EXPECTED_EMBED_DIM} dims. Deleting stale cache and rebuilding..."
                )
                os.remove(self.embeddings_path)
            else:
                self.embeddings = cached
                logger.info(f"Loaded cached embeddings: {self.embeddings.shape}")
                return
        
        logger.info("Building embeddings for all assessments...")
        embeddings_list = []
        embedding_dim = None  # We will detect this from the first successful call
        
        for i, assessment in enumerate(self.assessments):
            text = build_assessment_text(assessment)
            emb = get_embedding_gemini(text, self.api_key)
            
            if emb is not None:
                embeddings_list.append(emb)
                if embedding_dim is None:
                    embedding_dim = len(emb)  # Detect 3072 or 768 automatically
            else:
                # If the very first one fails, we use a temporary placeholder
                # If later ones fail, we use the detected dimension
                placeholder_dim = embedding_dim if embedding_dim else 3072
                embeddings_list.append(np.zeros(placeholder_dim, dtype=np.float32))
                logger.warning(f"Failed to embed index {i}, using zero-vector fallback.")
            
            if (i + 1) % 50 == 0:
                logger.info(f"Embedded {i+1}/{len(self.assessments)}")
        
        # Convert to a clean numpy array
        self.embeddings = np.array(embeddings_list, dtype=np.float32)
        np.save(self.embeddings_path, self.embeddings)
        logger.info(f"Saved embeddings successfully: {self.embeddings.shape}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[int, float]]:
        """Search for top-k most similar assessments."""
        if self.embeddings is None:
            raise ValueError("Embeddings not built. Call build_embeddings() first.")
        
        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = cosine_similarity(query_embedding, emb)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# ---------------------------------------------------------------------------
# Query understanding with Gemini
# ---------------------------------------------------------------------------

def fetch_url_content(url: str) -> str:
    """Fetch text content from a URL (for JD URLs)."""
    try:
        resp = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=15)
        resp.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)[:4000]
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return ""


def expand_query_with_llm(query: str, api_key: str) -> str:
    """Use Gemini to expand and understand the query, extract key requirements."""
    # FIX: Pass key via params={} — base URL has no ?key= so there is no duplication
    prompt = f"""You are an expert HR assessment consultant. Given a job description or query, 
extract and expand the key requirements for assessment selection.

Query/JD: {query[:2000]}

Provide a comprehensive description of what assessments would be needed, including:
1. Technical skills required (if any)
2. Soft skills/behavioral competencies needed
3. Cognitive abilities required  
4. Domain knowledge areas
5. Estimated test duration preference (if mentioned)

Format as a rich paragraph that would help match against an assessment catalog.
Keep it under 300 words. Focus on keywords that would appear in assessment names and descriptions."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 400}
    }
    
    try:
        resp = requests.post(
            GEMINI_GENERATE_URL,
            params={"key": api_key},
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        expanded = resp.json()['candidates'][0]['content']['parts'][0]['text']
        logger.info(f"Query expanded: {expanded[:100]}...")
        return expanded
    except Exception as e:
        logger.error(f"Query expansion failed: {e}")
        return query


def rerank_with_llm(query: str, candidates: List[Dict], api_key: str, n: int = 10) -> List[Dict]:
    """Use Gemini to rerank and filter candidates based on the query."""
    # FIX: Pass key via params={} — base URL has no ?key= so there is no duplication
    candidate_text = "\n".join([
        f"{i+1}. {c['name']} (Types: {', '.join(c.get('test_type', []))}, Duration: {c.get('duration', 'N/A')} min, URL: {c['url']})"
        for i, c in enumerate(candidates)
    ])
    
    prompt = f"""You are an expert HR assessment consultant for SHL. 
Given the following job query and list of candidate assessments, select the BEST {n} assessments.

Job Query/Description:
{query[:2000]}

Available Assessments:
{candidate_text}

Instructions:
1. Select between 5-{n} most relevant assessments
2. Ensure BALANCE: if the query needs both technical and behavioral skills, include BOTH types
3. Consider duration constraints if mentioned in the query
4. Prefer assessments that directly match the role and required skills
5. Return ONLY a JSON array of numbers (1-based indices) of selected assessments

Example: [1, 3, 5, 7, 8, 12, 15]

Return ONLY the JSON array, nothing else:"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 100}
    }
    
    try:
        resp = requests.post(
            GEMINI_GENERATE_URL,
            params={"key": api_key},
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        result_text = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Parse JSON array
        match = re.search(r'\[[\d,\s]+\]', result_text)
        if match:
            indices = json.loads(match.group())
            selected = []
            for idx in indices:
                if 1 <= idx <= len(candidates):
                    selected.append(candidates[idx - 1])
            return selected[:n]
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
    
    # Fallback: return top candidates
    return candidates[:n]


def extract_duration_constraint(query: str) -> Optional[int]:
    """Extract duration constraint from query."""
    patterns = [
        r'(\d+)\s*(?:minute|min)',
        r'(?:within|under|max(?:imum)?|at most|no more than)\s*(\d+)\s*(?:hour|hr)',
        r'(\d+)\s*(?:hour|hr)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.I)
        if match:
            val = int(match.group(1))
            if 'hour' in pattern or 'hr' in pattern:
                val *= 60
            return val
    return None


# ---------------------------------------------------------------------------
# Main recommendation engine
# ---------------------------------------------------------------------------

class RecommendationEngine:
    """Main recommendation engine combining embedding search + LLM reranking."""
    
    def __init__(self, catalog_path: str = CATALOG_PATH, api_key: str = ""):
        self.api_key = api_key or GEMINI_API_KEY
        self.catalog_manager = CatalogManager(catalog_path, self.api_key)
        self._initialized = False
    
    def initialize(self):
        """Load catalog and build embeddings."""
        self.catalog_manager.load_catalog()
        self.catalog_manager.build_embeddings()
        self._initialized = True
        logger.info("Recommendation engine initialized")
    
    def recommend(self, query: str, n: int = 10, use_llm_rerank: bool = True) -> List[Dict]:
        """
        Get assessment recommendations for a query.
        
        Args:
            query: Natural language query, JD text, or URL
            n: Number of recommendations (5-10)
            use_llm_rerank: Whether to use LLM for reranking
        
        Returns:
            List of recommended assessment dicts
        """
        if not self._initialized:
            self.initialize()
        
        n = max(5, min(10, n))
        
        # Handle URL input
        if query.startswith('http://') or query.startswith('https://'):
            logger.info(f"Fetching JD from URL: {query}")
            url_content = fetch_url_content(query)
            if url_content:
                query = url_content
        
        # Extract duration constraint
        duration_limit = extract_duration_constraint(query)
        logger.info(f"Duration constraint: {duration_limit} minutes" if duration_limit else "No duration constraint")
        
        # Expand query with LLM
        if self.api_key:
            expanded_query = expand_query_with_llm(query, self.api_key)
        else:
            expanded_query = query
        
        # Get embedding for the expanded query
        query_embedding = get_embedding_gemini(expanded_query, self.api_key)
        if query_embedding is None:
            # Fallback: simple keyword-based ranking
            return self._keyword_fallback(query, n, duration_limit)
        
        # Get top candidates via embedding similarity
        top_k = min(30, len(self.catalog_manager.assessments))
        similar = self.catalog_manager.search(query_embedding, top_k=top_k)
        
        # Apply duration filter if needed
        candidates = []
        for idx, score in similar:
            assessment = self.catalog_manager.assessments[idx].copy()
            assessment['_score'] = float(score)
            
            # Apply duration constraint
            if duration_limit and assessment.get('duration'):
                if assessment['duration'] > duration_limit:
                    continue
            
            candidates.append(assessment)
        
        if len(candidates) < n:
            # Relax duration constraint if not enough candidates
            candidates = [
                {**self.catalog_manager.assessments[idx], '_score': float(score)}
                for idx, score in similar
            ]
        
        # LLM reranking
        if use_llm_rerank and self.api_key and len(candidates) > n:
            final = rerank_with_llm(query, candidates[:25], self.api_key, n)
        else:
            # Balance by test type
            final = self._balance_by_type(candidates, n, query)
        
        # Clean up internal fields and return
        result = []
        for a in final:
            clean = {
                'name': a.get('name', ''),
                'url': a.get('url', ''),
                'adaptive_support': a.get('adaptive_support', 'No'),
                'description': a.get('description', ''),
                'duration': a.get('duration', 0) or 0,
                'remote_support': a.get('remote_support', 'Yes'),
                'test_type': a.get('test_type', [])
            }
            result.append(clean)
        
        return result[:n]
    
    def _balance_by_type(self, candidates: List[Dict], n: int, query: str) -> List[Dict]:
        """Balance recommendations across test types based on query needs."""
        query_lower = query.lower()
        
        # Determine which types are needed
        needs_technical = any(kw in query_lower for kw in [
            'java', 'python', 'sql', 'javascript', 'coding', 'programming',
            'developer', 'engineer', 'technical', 'data', 'analytics'
        ])
        needs_cognitive = any(kw in query_lower for kw in [
            'cognitive', 'aptitude', 'reasoning', 'analyst', 'analytical'
        ])
        needs_behavioral = any(kw in query_lower for kw in [
            'collaborat', 'communicat', 'leadership', 'team', 'personality',
            'behavior', 'soft skill', 'interpersonal', 'sales', 'manager'
        ])
        
        # Group candidates by type
        technical  = [c for c in candidates if any(t in ['Knowledge & Skills'] for t in c.get('test_type', []))]
        cognitive  = [c for c in candidates if any(t in ['Ability & Aptitude'] for t in c.get('test_type', []))]
        behavioral = [c for c in candidates if any(t in ['Personality & Behavior', 'Competencies'] for t in c.get('test_type', []))]
        other      = [c for c in candidates if not any(t in ['Knowledge & Skills', 'Ability & Aptitude', 'Personality & Behavior', 'Competencies'] for t in c.get('test_type', []))]
        
        result = []
        
        if needs_technical and needs_behavioral:
            # Equal split
            result.extend(technical[:4])
            result.extend(behavioral[:3])
            result.extend(cognitive[:2])
            result.extend(other[:1])
        elif needs_technical:
            result.extend(technical[:6])
            result.extend(cognitive[:2])
            result.extend(other[:2])
        elif needs_behavioral:
            result.extend(behavioral[:5])
            result.extend(cognitive[:3])
            result.extend(other[:2])
        elif needs_cognitive:
            result.extend(cognitive[:5])
            result.extend(behavioral[:3])
            result.extend(other[:2])
        else:
            result = candidates[:n]
        
        # Fill up to n with remaining candidates
        seen = set(id(r) for r in result)
        for c in candidates:
            if len(result) >= n:
                break
            if id(c) not in seen:
                result.append(c)
                seen.add(id(c))
        
        return result[:n]
    
    def _keyword_fallback(self, query: str, n: int, duration_limit: Optional[int]) -> List[Dict]:
        """Simple keyword-based fallback when embedding is unavailable."""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        scored = []
        for assessment in self.catalog_manager.assessments:
            text = build_assessment_text(assessment).lower()
            text_words = set(re.findall(r'\b\w+\b', text))
            overlap = len(query_words & text_words)
            
            if duration_limit and assessment.get('duration'):
                if assessment['duration'] > duration_limit:
                    continue
            
            scored.append((assessment, overlap))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [a for a, _ in scored[:n]]


# ---------------------------------------------------------------------------
# Singleton engine instance
# ---------------------------------------------------------------------------

_engine: Optional[RecommendationEngine] = None


def get_engine(catalog_path: str = CATALOG_PATH, api_key: str = "") -> RecommendationEngine:
    """Get or create the singleton engine instance."""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine(catalog_path, api_key)
        _engine.initialize()
    return _engine
