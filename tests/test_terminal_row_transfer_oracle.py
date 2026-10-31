"""Third counting oracle: row-transfer DP, independent of inclusion-exclusion."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from terminal_row_transfer_oracle import count_nonterminal_boards


def test_exact_full_25_cube_terminal_complement_independent_row_dp():
    nonterminal, both_colors = count_nonterminal_boards()
    assert nonterminal == 768_416_499_589
    assert both_colors == 768_368_824_944
    assert 3**25 - nonterminal == 78_872_109_854
