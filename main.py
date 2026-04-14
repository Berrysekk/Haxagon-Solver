# main.py
"""
Haxagon CTF automation runner.
Usage: python main.py [--phase 1|2|3|4] [--dry-run]
"""
import asyncio
import argparse
import importlib
import sys

from browser import HaxagonBrowser
from state import State
from registry import get_solver

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
                importlib.import_module(mod)
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
            if state.is_solved(slug):
                print(f"[skip] {ch['name']} — already solved")
                continue
            if state.is_skipped(slug):
                print(f"[skip] {ch['name']} — marked skipped")
                continue

            solver = get_solver(slug)
            if not solver:
                print(f"[no solver] {ch['name']} ({slug})")
                continue

            print(f"[solving] {ch['name']} ({slug}, {ch['xp']}xp)...")
            ctx = await browser.open_challenge(slug)

            try:
                if asyncio.iscoroutinefunction(solver):
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

            print(f"  [flag] {flag}")
            if dry_run:
                print("  [dry-run] Not submitting.")
                continue

            accepted = await browser.submit_flag(slug, flag)
            if accepted:
                state.mark_solved(slug, flag=flag, xp=ch["xp"])
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
