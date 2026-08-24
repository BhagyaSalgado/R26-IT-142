"""Helper Functions"""

import json
from datetime import datetime
from typing import Any, Dict, List


def serialize_response(data: Any) -> str:
    """Serialize data to JSON with datetime support"""
    
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    return json.dumps(data, cls=DateTimeEncoder)


def format_percentage(value: float, decimals: int = 1) -> float:
    """Format percentage value"""
    return round(value, decimals)


def calculate_statistics(values: List[float]) -> Dict:
    """Calculate statistics for a list of values"""
    if not values:
        return {'mean': 0, 'min': 0, 'max': 0}
    
    return {
        'mean': round(sum(values) / len(values), 2),
        'min': min(values),
        'max': max(values),
        'count': len(values)
    }


def batch_list(items: List, batch_size: int) -> List[List]:
    """Split list into batches"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries"""
    result = dict1.copy()
    result.update(dict2)
    return result
