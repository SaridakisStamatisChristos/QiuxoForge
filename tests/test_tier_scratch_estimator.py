"""Structural capacity estimator properties, independent of the enumerator."""
import sys
from pathlib import Path
from math import comb
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from estimate_tier_scratch import capacity_plan, layer_bitmap_bytes, tier_universe


def test_exact_multinomial_layer_capacity_0_to_25():
    for k in range(26):
        assert sum(tier_universe(x, k-x) for x in range(k+1)) == 2*comb(25,k)*(2**k)
        assert layer_bitmap_bytes(k) >= (2*comb(25,k)*(2**k)+7)//8


def test_scratch_capacity_is_conservative_and_explicit():
    p=capacity_plan(11)
    assert len(p["occupancies"])==12
    assert p["fifo_buffer_ram_bytes"]==524288
    assert p["upper_bound_not_memory_measurement"] is True
    assert p["largest_structural_scratch_upper_bound_bytes"]>0
    for row in p["occupancies"]:
        assert row["combined_scratch_bytes_conservative_upper_bound"] == (
            row["bitmap_file_bytes_all_color_tiers"]
            +row["next_level_bitmap_file_bytes"]
            +row["largest_tier_fifo_bytes_structural_upper_bound"]
        )


def test_invalid_capacity_options():
    for k in (-1, 26, True, None, 2.5):
        with pytest.raises(ValueError):
            capacity_plan(k)
