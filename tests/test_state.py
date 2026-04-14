# tests/test_state.py
import pytest
from state import State

def test_mark_solved_persists(tmp_path):
    s = State(path=str(tmp_path / ".state.json"))
    s.mark_solved("level0", flag="CTF{tutorial}", xp=5)
    s2 = State(path=str(tmp_path / ".state.json"))
    assert s2.is_solved("level0")
    assert s2.get_flag("level0") == "CTF{tutorial}"

def test_mark_skipped(tmp_path):
    s = State(path=str(tmp_path / ".state.json"))
    s.mark_skipped("hard_challenge")
    assert s.is_skipped("hard_challenge")
    assert not s.is_solved("hard_challenge")

def test_total_xp_sums_correctly(tmp_path):
    s = State(path=str(tmp_path / ".state.json"))
    s.mark_solved("a", flag="CTF{a}", xp=10)
    s.mark_solved("b", flag="CTF{b}", xp=20)
    assert "XP: 30" in s.summary()

def test_skipped_not_duplicated(tmp_path):
    s = State(path=str(tmp_path / ".state.json"))
    s.mark_skipped("x")
    s.mark_skipped("x")
    assert s._data["skipped"].count("x") == 1
