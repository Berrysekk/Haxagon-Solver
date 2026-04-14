# solvers/phase4_skilled.py
"""Phase 4 Skilled/Expert — stubs requiring manual work."""
from registry import register


@register("backroom")
async def backroom(ctx: dict) -> str | None:
    """Web exploitation — requires manual analysis."""
    return None


@register("keylogger")
def keylogger(ctx: dict) -> str | None:
    """Malware analysis — requires manual work."""
    return None


@register("journey-around-the-world")
def journey_world(ctx: dict) -> str | None:
    """GeoOSINT — requires human judgment."""
    return None
