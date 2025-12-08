from __future__ import annotations
from typing import Any, Dict, List, Tuple, Iterable, Optional, Union

Path = str
Op = Dict[str, Any]
Delta = List[Op]

def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _num_equal(a: Any, b: Any, eps: float) -> bool:
    if _is_num(a) and _is_num(b):
        return abs(float(a) - float(b)) <= eps
    return a == b

def _join(parent: Path, key: Union[str, int]) -> Path:
    # JSON Pointer-ish path
    esc = str(key).replace("~", "~0").replace("/", "~1")
    return parent + "/" + esc if parent else "/" + esc

def _deep_diff(
    old: Any,
    new: Any,
    path: Path,
    *,
    epsilon: float,
    ignore_keys: Iterable[str]
) -> Delta:
    ops: Delta = []

    # Dicts
    if isinstance(old, dict) and isinstance(new, dict):
        old_keys = set(old.keys()) - set(ignore_keys)
        new_keys = set(new.keys()) - set(ignore_keys)

        # Removed keys
        for k in sorted(old_keys - new_keys):
            ops.append({"op": "remove", "path": _join(path, k), "old": old[k]})

        # Added keys
        for k in sorted(new_keys - old_keys):
            ops.append({"op": "add", "path": _join(path, k), "new": new[k]})

        # Changed keys
        for k in sorted(old_keys & new_keys):
            ops.extend(_deep_diff(old[k], new[k], _join(path, k),
                                  epsilon=epsilon, ignore_keys=ignore_keys))
        return ops

    # Lists
    if isinstance(old, list) and isinstance(new, list):
        # Simple list strategy: index-by-index replace/add/remove.
        # (If you later need smarter diffs, we can switch to LCS.)
        min_len = min(len(old), len(new))
        for i in range(min_len):
            ops.extend(_deep_diff(old[i], new[i], _join(path, i),
                                  epsilon=epsilon, ignore_keys=ignore_keys))
        # Tail adds
        for i in range(min_len, len(new)):
            ops.append({"op": "add", "path": _join(path, i), "new": new[i]})
        # Tail removes (from end to start to keep indices valid when applying)
        for i in range(len(old) - 1, min_len - 1, -1):
            ops.append({"op": "remove", "path": _join(path, i), "old": old[i]})
        return ops

    # Scalars or mismatched types
    if not _num_equal(old, new, eps=epsilon):
        ops.append({"op": "replace", "path": path or "/", "old": old, "new": new})
    return ops


def calculate_world_delta(
    old_world: Dict[str, Any],
    new_world: Dict[str, Any],
    *,
    epsilon: float = 1e-6,
    ignore_keys: Iterable[str] = ()
) -> Delta:
    """
    Deep diff between two world states.
    Returns a list of operations: add/remove/replace with JSON-pointer-like paths.
    """
    return _deep_diff(old_world, new_world, "", epsilon=epsilon, ignore_keys=tuple(ignore_keys))


# ---------- APPLY ----------

def _path_tokens(path: Path) -> List[str]:
    if not path or path == "/":
        return []
    if not path.startswith("/"):
        raise ValueError(f"Invalid path '{path}' (must start with '/')")
    parts = path.split("/")[1:]
    return [p.replace("~1", "/").replace("~0", "~") for p in parts]

def _ensure_container(parent: Any, key: str) -> None:
    if isinstance(parent, dict):
        return
    raise TypeError(f"Cannot set key '{key}' on non-dict parent: {type(parent).__name__}")

def _navigate(root: Any, tokens: List[str]) -> Tuple[Any, Optional[str]]:
    """
    Returns (parent_container, last_token) to apply an op at the final token.
    If tokens empty, returns (root, None) for root-level replace.
    """
    if not tokens:
        return root, None
    cur = root
    for t in tokens[:-1]:
        if isinstance(cur, dict):
            if t not in cur or not isinstance(cur[t], (dict, list)):
                # auto-create intermediate dicts to be robust
                cur[t] = {}
            cur = cur[t]
        elif isinstance(cur, list):
            idx = int(t)
            if idx < 0 or idx >= len(cur):
                raise IndexError(f"List index out of range while navigating: {t}")
            cur = cur[idx]
        else:
            raise TypeError(f"Cannot navigate through type: {type(cur).__name__}")
    return cur, tokens[-1]

def _apply_add(parent: Any, key: Optional[str], value: Any) -> None:
    if key is None:
        raise ValueError("Cannot 'add' at root without key")
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        idx = int(key)
        if idx == len(parent):
            parent.append(value)
        elif 0 <= idx < len(parent):
            parent.insert(idx, value)
        else:
            raise IndexError(f"List index out of range for add: {idx}")
    else:
        raise TypeError(f"Cannot add on parent type: {type(parent).__name__}")

def _apply_remove(parent: Any, key: Optional[str]) -> Any:
    if key is None:
        raise ValueError("Cannot 'remove' the entire root")
    if isinstance(parent, dict):
        return parent.pop(key)
    elif isinstance(parent, list):
        idx = int(key)
        return parent.pop(idx)
    else:
        raise TypeError(f"Cannot remove on parent type: {type(parent).__name__}")

def _apply_replace(parent: Any, key: Optional[str], value: Any) -> None:
    if key is None:
        # Replace root entirely — only allowed if parent is a dict-like.
        if isinstance(parent, dict):
            parent.clear()
            if isinstance(value, dict):
                parent.update(value)
            else:
                raise TypeError("Root replace requires dict new value")
            return
        raise TypeError("Root replace unsupported for non-dict root")
    if isinstance(parent, dict):
        parent[key] = value
    elif isinstance(parent, list):
        idx = int(key)
        parent[idx] = value
    else:
        raise TypeError(f"Cannot replace on parent type: {type(parent).__name__}")

def apply_world_delta(world: Dict[str, Any], delta: Delta) -> Dict[str, Any]:
    """
    Applies the op list to 'world' in-place and returns it.
    """
    for op in delta:
        op_type = op.get("op")
        path = op.get("path", "/")
        tokens = _path_tokens(path)
        parent, last = _navigate(world, tokens)

        if op_type == "add":
            _apply_add(parent, last, op["new"])
        elif op_type == "remove":
            _apply_remove(parent, last)
        elif op_type == "replace":
            _apply_replace(parent, last, op["new"])
        else:
            raise ValueError(f"Unknown op: {op_type}")
    return world
