from ansibleplaybookgrapher.utils import merge_dicts


def test_merge_dicts() -> None:
    """Test dicts grouping.
    :return:
    """
    res = merge_dicts({"1": {2, 3}, "4": {5}, "9": [11]}, {"4": {7}, "9": set()})
    assert res == {"1": {2, 3}, "4": {5, 7}, "9": {11}}
