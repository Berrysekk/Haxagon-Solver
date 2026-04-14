"""Smoke tests: all solver modules import cleanly and all solvers are callable."""
import importlib
import pytest


SOLVER_MODULES = [
    "solvers.phase1_simple",
    "solvers.phase2_beginner",
    "solvers.phase3_average",
    "solvers.phase4_skilled",
]


@pytest.mark.parametrize("mod", SOLVER_MODULES)
def test_solver_module_imports(mod):
    """Each solver module must import without errors."""
    importlib.import_module(mod)


def test_all_registered_solvers_are_callable():
    """Every slug registered via @register must map to a callable."""
    # Import all modules to populate registry
    for mod in SOLVER_MODULES:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            pass
    from registry import list_solvers, get_solver
    slugs = list_solvers()
    assert len(slugs) > 0, "No solvers registered"
    for slug in slugs:
        fn = get_solver(slug)
        assert callable(fn), f"Solver for '{slug}' is not callable"


def test_registry_does_not_return_none_for_known_slugs():
    """Spot-check a few known slugs are registered."""
    from registry import get_solver
    known = ["level0", "what-is-my-ip", "html-maze", "0-f", "agent-007"]
    for slug in known:
        assert get_solver(slug) is not None, f"Expected solver for '{slug}' to be registered"
