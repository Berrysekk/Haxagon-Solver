# main.py
"""
Haxagon CTF automation runner.
Usage: python main.py [--phase 1|2|3|4] [--dry-run]
"""
import asyncio
import argparse
import importlib
import inspect
import re
import sys

from browser import HaxagonBrowser
from state import State
from registry import get_solver


def name_to_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')

CREDENTIALS = {
    "email": "beranek.ja.2024@skola.ssps.cz",
    "password": "HonzaB_2009_",
}

PHASE_MODULES = {
    1: "solvers.phase1_simple",
    2: "solvers.phase2_beginner",
    3: "solvers.phase3_average",
    4: "solvers.phase4_skilled",
}


async def run(phases: list[int], dry_run: bool):
    for phase in phases:
        mod = PHASE_MODULES.get(phase)
        if mod:
            try:
                importlib.import_module(mod)  # nosemgrep — module name comes from a fixed allowlist (PHASE_MODULES / EnumType.value)
            except ModuleNotFoundError as e:
                print(f"[warn] Could not load phase {phase}: {e}")

    state = State()
    print(f"Starting. Current state: {state.summary()}")

    async with HaxagonBrowser() as browser:
        ok = await browser.login(CREDENTIALS["email"], CREDENTIALS["password"])
        if not ok:
            print("[error] Login failed. Check credentials or site selectors.")
            sys.exit(1)
        print("[ok] Logged in.")

        challenges = await browser.list_challenges()
        print(f"Found {len(challenges)} challenges.")

        for ch in challenges:
            slug = ch["slug"]
            if ch.get("solved"):
                continue  # already solved on platform, no XP left to earn
            if state.is_solved(slug):
                print(f"[skip] {ch['name']} — already solved")
                continue
            if state.is_skipped(slug):
                print(f"[skip] {ch['name']} — marked skipped")
                continue

            solver = get_solver(slug) or get_solver(name_to_slug(ch["name"]))
            if not solver:
                print(f"[no solver] {ch['name']} ({slug})")
                continue

            print(f"[solving] {ch['name']} ({slug}, {ch['xp']}xp)...")
            ctx = await browser.open_challenge(slug)

            try:
                if inspect.iscoroutinefunction(solver):
                    flag = await solver(ctx)
                else:
                    flag = solver(ctx)
            except Exception as e:
                print(f"  [error] {e}")
                state.mark_skipped(slug)
                continue

            if not flag:
                print(f"  [no flag returned] — skipping")
                state.mark_skipped(slug)
                continue

            # Normalise to list; single-flag challenges return a string
            flags = flag if isinstance(flag, list) else [flag]
            print(f"  [flag] {flags[0]}" + (f" (+{len(flags)-1} more)" if len(flags) > 1 else ""))
            if dry_run:
                print("  [dry-run] Not submitting.")
                continue

            if len(flags) == 1:
                accepted = await browser.submit_flag(slug, flags[0])
            else:
                accepted = await browser.submit_multi_flags(slug, flags)

            if accepted:
                state.mark_solved(slug, flag=flags[0], xp=ch["xp"])
                print(f"  [accepted] +{ch['xp']} XP")
            else:
                print(f"  [rejected] Flag was wrong or submit failed.")
                state.mark_skipped(slug)

    print(f"\nDone. {state.summary()}")


def main():
    parser = argparse.ArgumentParser(description="Haxagon CTF solver")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run specific phase only")
    parser.add_argument("--dry-run", action="store_true", help="Solve but don't submit")
    args = parser.parse_args()
    phases = [args.phase] if args.phase else [1, 2, 3, 4]
    asyncio.run(run(phases, args.dry_run))


if __name__ == "__main__":
    main()
