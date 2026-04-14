# tests/test_registry.py
from registry import register, get_solver, list_solvers

def test_register_and_retrieve():
    @register("test-slug")
    def my_solver(ctx): return "CTF{flag}"
    assert get_solver("test-slug") is my_solver

def test_unknown_slug_returns_none():
    assert get_solver("nonexistent-xyz-abc") is None

def test_register_returns_original_function():
    @register("test-slug-2")
    def solver(ctx): return None
    assert callable(solver)

def test_list_solvers_includes_registered():
    @register("listed-slug")
    def s(ctx): pass
    assert "listed-slug" in list_solvers()
