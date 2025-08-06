"""
JSON utilities for handling UUID and other non-serializable types
"""

import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID, datetime, and other types."""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def json_serializable(obj: Any) -> Any:
    """Convert object to JSON serializable format."""
    if isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [json_serializable(item) for item in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__dict__'):
        return json_serializable(obj.__dict__)
    else:
        return obj


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON string."""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


def safe_json_loads(s: str, **kwargs) -> Any:
    """Safely deserialize JSON string to object."""
    return json.loads(s, **kwargs)