from validations.checks import ValueOverlapCheck

def _check():
    return ValueOverlapCheck(None, None, None, [])

def test_overlap_empty_prod_returns_none():
    assert _check()._calculate_overlap(set(), {1}) is None

def test_overlap_with_leak():
    metrics = _check()._calculate_overlap({1, 2}, {2, 3})
    assert metrics["leaks_count"] == 1
    assert metrics["overlap_ratio"] == 50.0
    assert metrics["prod_distinct_count"] == 2
    assert metrics["dev_distinct_count"] == 2

def test_overlap_no_leak():
    metrics = _check()._calculate_overlap({1, 2}, {3, 4})
    assert metrics["leaks_count"] == 0
    assert metrics["overlap_ratio"] == 0.0
    assert metrics["prod_distinct_count"] == 2
    assert metrics["dev_distinct_count"] == 2