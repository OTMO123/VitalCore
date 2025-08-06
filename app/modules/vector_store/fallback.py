"""
Vector Store Fallback Mechanisms

Enterprise-grade fallback and graceful degradation for vector database operations
when primary Milvus service is unavailable.
"""

import asyncio
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import structlog
from pathlib import Path

from app.core.config import get_settings
from .schemas import SimilarCase, VectorOperationResult, AnonymizedMLProfile
from .metrics import vector_metrics

logger = structlog.get_logger(__name__)


class VectorStoreFallback:
    """
    Fallback service for vector store operations when Milvus is unavailable.
    
    Provides graceful degradation with local caching, simple similarity search,
    and service recovery detection.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logger.bind(component="VectorStoreFallback")
        
        # Fallback storage paths
        self.cache_dir = Path("/tmp/vector_store_fallback")
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache for recent operations
        self.vector_cache: Dict[str, Dict[str, Any]] = {}
        self.search_cache: Dict[str, List[SimilarCase]] = {}
        
        # Cache settings
        self.max_cache_size = 1000
        self.cache_ttl_hours = 24
        
        # Fallback statistics
        self.fallback_stats = {
            "fallback_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "approximate_results": 0,
            "service_unavailable_responses": 0
        }
        
        self.logger.info(
            "Vector store fallback service initialized",
            cache_dir=str(self.cache_dir),
            max_cache_size=self.max_cache_size
        )
    
    async def handle_search_fallback(
        self,
        query_vector: List[float],
        collection: str = "healthcare_vectors",
        top_k: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[SimilarCase]:
        """
        Fallback similarity search using cached data.
        
        When Milvus is unavailable, performs approximate similarity search
        using cached vectors and basic cosine similarity.
        """
        try:
            self.fallback_stats["fallback_searches"] += 1
            vector_metrics.record_operation("fallback_search", collection, 0.0, "fallback")
            
            # Check cache first
            cache_key = self._generate_cache_key(query_vector, collection, top_k)
            if cache_key in self.search_cache:
                self.fallback_stats["cache_hits"] += 1
                vector_metrics.record_cache_hit("fallback_search")
                
                self.logger.info(
                    "Returning cached fallback search results",
                    cache_key=cache_key[:16],
                    collection=collection
                )
                return self.search_cache[cache_key]
            
            self.fallback_stats["cache_misses"] += 1
            vector_metrics.record_cache_miss("fallback_search")
            
            # Load cached vectors from disk
            cached_vectors = await self._load_cached_vectors(collection)
            
            if not cached_vectors:
                self.fallback_stats["service_unavailable_responses"] += 1
                self.logger.warning(
                    "No cached vectors available for fallback search",
                    collection=collection
                )
                return self._create_service_unavailable_response()
            
            # Perform approximate similarity search
            start_time = datetime.utcnow()
            similar_cases = await self._approximate_similarity_search(
                query_vector, cached_vectors, top_k, similarity_threshold
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Cache results
            self.search_cache[cache_key] = similar_cases
            self._cleanup_cache()
            
            self.fallback_stats["approximate_results"] += 1
            vector_metrics.record_search(collection, len(similar_cases), similarity_threshold, True)
            
            self.logger.info(
                "Fallback search completed",
                collection=collection,
                results_count=len(similar_cases),
                processing_time_ms=processing_time * 1000,
                similarity_threshold=similarity_threshold
            )
            
            return similar_cases
            
        except Exception as e:
            self.logger.error(
                "Fallback search failed",
                error=str(e),
                collection=collection
            )
            vector_metrics.record_operation("fallback_search", collection, 0.0, "error")
            return self._create_error_response(str(e))
    
    async def handle_indexing_fallback(
        self,
        profiles: List[AnonymizedMLProfile]
    ) -> VectorOperationResult:
        """
        Fallback indexing - cache vectors locally for future fallback searches.
        """
        try:
            collection = "healthcare_vectors"  # Default collection
            
            # Save to local cache
            cache_file = self.cache_dir / f"{collection}_vectors.pkl"
            
            # Load existing cache
            existing_vectors = []
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        existing_vectors = pickle.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load existing cache: {e}")
            
            # Add new vectors
            new_vectors = []
            for profile in profiles:
                if profile.clinical_text_embedding:
                    vector_data = {
                        "id": profile.anonymous_id,
                        "vector": profile.clinical_text_embedding,
                        "metadata": {
                            "medical_category": profile.medical_category,
                            "anonymization_level": profile.anonymization_level,
                            "cached_at": datetime.utcnow().isoformat()
                        }
                    }
                    new_vectors.append(vector_data)
            
            # Combine and save
            all_vectors = existing_vectors + new_vectors
            
            # Limit cache size
            if len(all_vectors) > self.max_cache_size:
                # Keep most recent vectors
                all_vectors = sorted(
                    all_vectors,
                    key=lambda x: x["metadata"]["cached_at"],
                    reverse=True
                )[:self.max_cache_size]
            
            # Save to disk
            with open(cache_file, 'wb') as f:
                pickle.dump(all_vectors, f)
            
            self.logger.info(
                "Vectors cached for fallback service",
                new_vectors=len(new_vectors),
                total_cached=len(all_vectors),
                cache_file=str(cache_file)
            )
            
            return VectorOperationResult(
                success=True,
                message=f"Vectors cached locally ({len(new_vectors)} new, {len(all_vectors)} total)",
                operation_id=f"fallback_{datetime.utcnow().timestamp()}",
                processing_time_ms=0,
                vectors_processed=len(profiles),
                metadata={"fallback_mode": True, "cache_location": str(cache_file)}
            )
            
        except Exception as e:
            self.logger.error("Fallback indexing failed", error=str(e))
            return VectorOperationResult(
                success=False,
                message=f"Fallback indexing failed: {str(e)}",
                operation_id="fallback_error",
                processing_time_ms=0,
                vectors_processed=0,
                metadata={"error": str(e)}
            )
    
    async def _load_cached_vectors(self, collection: str) -> List[Dict[str, Any]]:
        """Load cached vectors from disk"""
        cache_file = self.cache_dir / f"{collection}_vectors.pkl"
        
        if not cache_file.exists():
            return []
        
        try:
            with open(cache_file, 'rb') as f:
                vectors = pickle.load(f)
            
            # Filter out expired vectors
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_ttl_hours)
            valid_vectors = []
            
            for vector in vectors:
                cached_at = datetime.fromisoformat(vector["metadata"]["cached_at"])
                if cached_at > cutoff_time:
                    valid_vectors.append(vector)
            
            if len(valid_vectors) != len(vectors):
                # Save filtered vectors back
                with open(cache_file, 'wb') as f:
                    pickle.dump(valid_vectors, f)
                
                self.logger.info(
                    "Cleaned up expired cached vectors",
                    expired_count=len(vectors) - len(valid_vectors),
                    valid_count=len(valid_vectors)
                )
            
            return valid_vectors
            
        except Exception as e:
            self.logger.error(f"Failed to load cached vectors: {e}")
            return []
    
    async def _approximate_similarity_search(
        self,
        query_vector: List[float],
        cached_vectors: List[Dict[str, Any]],
        top_k: int,
        similarity_threshold: float
    ) -> List[SimilarCase]:
        """Perform approximate similarity search using cosine similarity"""
        import numpy as np
        
        results = []
        query_array = np.array(query_vector)
        query_norm = np.linalg.norm(query_array)
        
        for vector_data in cached_vectors:
            try:
                vector_array = np.array(vector_data["vector"])
                vector_norm = np.linalg.norm(vector_array)
                
                # Cosine similarity
                if query_norm > 0 and vector_norm > 0:
                    similarity = np.dot(query_array, vector_array) / (query_norm * vector_norm)
                    
                    if similarity >= similarity_threshold:
                        similar_case = SimilarCase(
                            case_id=vector_data["id"],
                            similarity_score=float(similarity),
                            medical_category=vector_data["metadata"].get("medical_category", "unknown"),
                            case_summary=f"Cached case (similarity: {similarity:.3f})",
                            metadata={
                                **vector_data["metadata"],
                                "fallback_search": True,
                                "approximate_similarity": True
                            }
                        )
                        results.append(similar_case)
                        
            except Exception as e:
                self.logger.warning(f"Error processing cached vector: {e}")
                continue
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]
    
    def _generate_cache_key(self, query_vector: List[float], collection: str, top_k: int) -> str:
        """Generate cache key for search results"""
        # Create hash from query vector (sample to avoid huge keys)
        vector_sample = query_vector[::max(1, len(query_vector) // 10)]  # Sample every 10th element
        key_data = f"{collection}:{top_k}:{vector_sample}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cleanup_cache(self):
        """Clean up in-memory cache if it gets too large"""
        if len(self.search_cache) > self.max_cache_size:
            # Remove oldest entries (simple FIFO)
            items_to_remove = len(self.search_cache) - self.max_cache_size + 100
            keys_to_remove = list(self.search_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self.search_cache[key]
            
            self.logger.info(f"Cleaned up {items_to_remove} cache entries")
    
    def _create_service_unavailable_response(self) -> List[SimilarCase]:
        """Create response indicating service is unavailable"""
        return [
            SimilarCase(
                case_id="service_unavailable",
                similarity_score=0.0,
                medical_category="system_message",
                case_summary="Vector store service temporarily unavailable. No cached data available for similarity search.",
                metadata={
                    "service_status": "unavailable",
                    "fallback_active": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        ]
    
    def _create_error_response(self, error_message: str) -> List[SimilarCase]:
        """Create error response"""
        return [
            SimilarCase(
                case_id="fallback_error",
                similarity_score=0.0,
                medical_category="system_error",
                case_summary=f"Fallback search error: {error_message}",
                metadata={
                    "error": error_message,
                    "fallback_active": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        ]
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get fallback service statistics"""
        return {
            **self.fallback_stats,
            "cache_size": len(self.search_cache),
            "cache_dir": str(self.cache_dir),
            "cache_ttl_hours": self.cache_ttl_hours,
            "max_cache_size": self.max_cache_size
        }

# Global fallback service instance
vector_fallback = VectorStoreFallback()