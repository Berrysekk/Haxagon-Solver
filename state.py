# state.py
import json
import os

class State:
    def __init__(self, path: str = ".state.json"):
        self._path = path
        self._data: dict = {"solved": {}, "skipped": [], "total_xp": 0}
        if os.path.exists(path):
            with open(path) as f:
                self._data = json.load(f)

    def _save(self):
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def mark_solved(self, slug: str, flag: str, xp: int = 0):
        self._data["solved"][slug] = {"flag": flag, "xp": xp}
        self._data["total_xp"] = sum(v["xp"] for v in self._data["solved"].values())
        self._save()

    def mark_skipped(self, slug: str):
        if slug not in self._data["skipped"]:
            self._data["skipped"].append(slug)
        self._save()

    def is_solved(self, slug: str) -> bool:
        return slug in self._data["solved"]

    def is_skipped(self, slug: str) -> bool:
        return slug in self._data["skipped"]

    def get_flag(self, slug: str) -> str | None:
        return self._data["solved"].get(slug, {}).get("flag")

    def summary(self) -> str:
        return (f"Solved: {len(self._data['solved'])} | "
                f"Skipped: {len(self._data['skipped'])} | "
                f"XP: {self._data['total_xp']}")
