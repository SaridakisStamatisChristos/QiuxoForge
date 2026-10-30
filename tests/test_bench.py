from quixoforge.bench import run, positions
from quixoforge.model import State


def test_seed_reproducibility_and_result_schema():
    assert positions(7,4,5) == positions(7,4,5)
    result = run(seed=7,count=3,plies=5,depth=1,repeats=1)
    assert result["seed"] == 7
    assert result["samples"] == 3
    assert result["implementations"]["bitboard"]["median_search_nodes"] > 0
