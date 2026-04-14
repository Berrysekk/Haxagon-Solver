# registry.py
_REGISTRY: dict[str, callable] = {}

def register(slug: str):
    """Decorator: @register('challenge-slug')"""
    def decorator(fn):
        _REGISTRY[slug] = fn
        return fn
    return decorator

def get_solver(slug: str):
    return _REGISTRY.get(slug)

def list_solvers() -> list[str]:
    return list(_REGISTRY.keys())
