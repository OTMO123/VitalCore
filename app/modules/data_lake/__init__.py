"""
Data Lake Module for Healthcare ML Platform

Provides MinIO S3-compatible data lake integration for ML training datasets
with HIPAA-compliant storage, lifecycle management, and vector database sync.
"""

try:
    from .minio_pipeline import MLDataLakePipeline, DataLakeConfig
    __all__ = ["MLDataLakePipeline", "DataLakeConfig"]
except ImportError:
    # Data lake dependencies not available - create placeholder classes
    class MLDataLakePipeline:
        def __init__(self, *args, **kwargs):
            raise ImportError("Data lake dependencies not available - install pyarrow, pandas, minio, boto3")
    
    class DataLakeConfig:
        def __init__(self, *args, **kwargs):
            raise ImportError("Data lake dependencies not available - install pyarrow, pandas, minio, boto3")
    
    __all__ = ["MLDataLakePipeline", "DataLakeConfig"]