"""Execute the exact global structural theorem and independent D4 oracle."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("source,expected", [
    ("terminal_orbit_bounds.cpp", (
        "structural_terminal_board_orbits=9860698038",
        "structural_terminal_board_turn_orbits=19721396076",
        "structural_nonterminal_both_colors_board_turn_orbits=192103543260",
        "reachable_nonterminal_board_turn_orbit_upper_bound=192103543264",
    )),
    ("terminal_bounds_by_occupancy.cpp", (
        "k,structural_terminal_board_turn_D4",
        "8,55680,68686026,68686026",
        "25,4583676,3839812,3839812",
    )),
    ("terminal_orbit_bruteforce.cpp", (
        "g=2 fixed_terminal=435502 fixed_nonterminal_both_colors=1149024",
        "g=4 fixed_terminal=4841478 fixed_nonterminal_both_colors=9475712",
        "PASS: seven independent direct D4 symmetry-fixed enumerations",
    )),
])
def test_exact_global_terminal_bounds(tmp_path, source, expected):
    compiler = shutil.which("c++")
    if compiler is None:
        pytest.skip("C++ compiler unavailable: theorem source independently executable")
    binary = tmp_path / "verify"
    subprocess.run([compiler, "-O3", "-std=c++17", "-Wall", "-Wextra",
                    "-pedantic", str(ROOT / "tools" / source), "-o", str(binary)],
                   check=True, capture_output=True, text=True, timeout=60)
    out = subprocess.run([str(binary)], check=True, capture_output=True,
                         text=True, timeout=120).stdout
    for line in expected:
        assert line in out
