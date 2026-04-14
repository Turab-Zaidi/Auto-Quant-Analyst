from typing import List, Any

def append_reducer(left: List[Any], right: List[Any]) -> List[Any]:
    """Appends new items to the existing list (e.g., for error logging)."""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right

def extend_reducer(left: List[str], right: List[str]) -> List[str]:
    """Extends a list with new items, avoiding duplicates (e.g., for file paths)."""
    if left is None:
        left = []
    if right is None:
        right = []
    # Preserve order but remove duplicates
    return list(dict.fromkeys(left + right))