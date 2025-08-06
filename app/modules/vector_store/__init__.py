"""
Vector Store Module for Healthcare ML Platform

Provides Milvus vector database integration for Clinical BERT embeddings
with HIPAA-compliant similarity search and healthcare-specific operations.
"""

try:
    from .milvus_client import MilvusVectorStore, MilvusConfig, SimilarCase
    __all__ = ["MilvusVectorStore", "MilvusConfig", "SimilarCase"]
except ImportError:
    # Vector store dependencies not available - create placeholder classes
    class MilvusVectorStore:
        def __init__(self, *args, **kwargs):
            raise ImportError("pymilvus not available - vector store functionality disabled")
    
    class MilvusConfig:
        def __init__(self, *args, **kwargs):
            raise ImportError("pymilvus not available - vector store functionality disabled")
    
    class SimilarCase:
        def __init__(self, *args, **kwargs):
            raise ImportError("pymilvus not available - vector store functionality disabled")
    
    __all__ = ["MilvusVectorStore", "MilvusConfig", "SimilarCase"]