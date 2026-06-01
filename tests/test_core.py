import numpy as np

from tdms_sync_checker.core import value_stats, suggested_activity_trim, infer_test_id


def test_value_stats_constant():
    stats = value_stats(np.array([1.0, 1.0, 1.0]))
    assert stats["is_constant"] is True
    assert stats["is_changing"] is False


def test_value_stats_changing():
    stats = value_stats(np.array([0.0, 1.0, 2.0]))
    assert stats["is_constant"] is False
    assert stats["is_changing"] is True


def test_suggested_activity_trim_constant():
    trim = suggested_activity_trim(np.ones(10))
    assert trim["activity_status"] == "constant"
    assert trim["suggested_samples_removed_total"] == 0


def test_infer_test_id():
    assert infer_test_id(type("P", (), {"stem": "test_001"})()) == "test"
