import numpy as np
from src.embeddings import get_embedding_model
from src.logger import log_event
from config.config import CACHE_SIMILARITY_THRESHOLD, CACHE_FREQ_THRESHOLD

class FrequencySemanticCache:
    def __init__(self):
        self.embeddings = get_embedding_model()
        self.history = []

    async def check_cache(self, query: str):
        # Use async embedding to prevent blocking the event loop
        query_emb = await self.embeddings.aembed_query(query)
        query_emb_np = np.array(query_emb)
        
        best_match = None
        best_score = -1
        
        for item in self.history:
            item_emb_np = item['embedding']
            score = np.dot(query_emb_np, item_emb_np) / (np.linalg.norm(query_emb_np) * np.linalg.norm(item_emb_np))
            if score > best_score:
                best_score = score
                best_match = item
                
        if best_match and best_score >= CACHE_SIMILARITY_THRESHOLD:
            best_match['count'] += 1
            
            if best_match['count'] >= CACHE_FREQ_THRESHOLD and best_match['response'] is not None:
                await log_event("CACHE_HIT", {"query": query, "matched_query": best_match['query'], "score": float(best_score), "count": best_match['count']})
                return True, best_match['response'], best_match
            else:
                await log_event("CACHE_MISS_THRESHOLD_NOT_MET", {"query": query, "matched_query": best_match['query'], "score": float(best_score), "count": best_match['count']})
                return False, None, best_match
        else:
            new_item = {
                'query': query,
                'embedding': query_emb_np,
                'count': 1,
                'response': None
            }
            self.history.append(new_item)
            await log_event("CACHE_MISS_NEW_QUERY", {"query": query})
            return False, None, new_item

    def save_response(self, item, response: str):
        # Always store the latest response, but we only serve it if count >= CACHE_FREQ_THRESHOLD
        item['response'] = response

semantic_cache = FrequencySemanticCache()
