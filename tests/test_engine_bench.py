import pytest
from quixoforge.engine_bench import run


def test_fair_semantic_benchmark_smoke():
    report=run(seed=917,count=2,plies=6,depth=1,repeats=1)
    assert report["samples"]==2
    assert report["implementations"]["independent_brute"]["median_nodes"]>0
    with pytest.raises(ValueError):run(depth=4)
    with pytest.raises(ValueError):run(repeats=0)
