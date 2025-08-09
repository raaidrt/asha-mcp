import sys
import types
from pathlib import Path
import pytest


@pytest.fixture(autouse=True, scope='session')
def setup_fake_stockfish_and_bin():
    # Ensure a dummy binary exists so asha's module-level path discovery succeeds
    repo_root = Path(__file__).resolve().parents[1]
    bin_dir = repo_root / 'src/asha/stockfish_bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    for file in bin_dir.iterdir():
        file.unlink()

    dummy_bin = bin_dir / 'dummy_stockfish'
    dummy_bin.touch(exist_ok=True)

    # Provide a fake stockfish module to avoid requiring a real engine
    fake_stockfish = types.ModuleType('stockfish')

    class FakeStockfish:
        def __init__(self, path: str):
            self.path = path

        def set_fen_position(self, fen: str):
            pass

        def set_depth(self, depth: int):
            pass

        def get_evaluation(self):
            return {'type': 'cp', 'value': 0}

    fake_stockfish.Stockfish = FakeStockfish
    sys.modules['stockfish'] = fake_stockfish

    yield

    # remove all files in bin_dir
    bin_dir = Path(__file__).resolve().parents[1] / 'src/asha/stockfish_bin'
    for file in bin_dir.iterdir():
        file.unlink()


@pytest.fixture(scope='session')
def asha_module():
    import importlib

    asha = importlib.import_module('asha')
    return asha


def test_eval_str_formatting(asha_module):
    Eval = asha_module.Eval
    assert str(Eval('cp', True, 0)) == 'CP[0]'
    assert str(Eval('mate', False, 3)) == 'Mate[3]'


@pytest.mark.parametrize(
    'lhs, rhs, expected_lhs_lt_rhs, expected_rhs_lt_lhs',
    [
        # cp vs cp, white to move: higher cp is better (sorts earlier), so 1 < 0
        (('cp', True, 1), ('cp', True, 0), True, False),
        # cp vs cp, black to move: lower cp is better, so 0 < 1
        (('cp', False, 0), ('cp', False, 1), True, False),
        # mate vs mate, white to move: smaller mate distance is better, so 3 < 5
        (('mate', True, 3), ('mate', True, 5), True, False),
        # mate vs mate, black to move: larger mate distance is better, so 5 < 3
        (('mate', False, 5), ('mate', False, 3), True, False),
        # cp vs mate: cp always considered less than mate
        (('cp', True, 0), ('mate', True, 3), True, False),
        (('cp', False, 0), ('mate', False, 3), True, False),
        # mate vs cp: inverse relation
        (('mate', True, 3), ('cp', True, 0), False, True),
        (('mate', False, 3), ('cp', False, 0), False, True),
        # equality cases
        (('cp', True, 0), ('cp', True, 0), False, False),
        (('mate', False, 4), ('mate', False, 4), False, False),
    ],
)
def test_eval_comparisons_table(asha_module, lhs, rhs, expected_lhs_lt_rhs, expected_rhs_lt_lhs):
    Eval = asha_module.Eval
    lhs_eval = Eval(*lhs)
    rhs_eval = Eval(*rhs)

    assert (lhs_eval < rhs_eval) is expected_lhs_lt_rhs
    assert (rhs_eval < lhs_eval) is expected_rhs_lt_lhs

    # Sorting should place the "smaller" one first
    sorted_pair = sorted([lhs_eval, rhs_eval])
    if expected_lhs_lt_rhs and not expected_rhs_lt_lhs:
        assert sorted_pair[0] is lhs_eval
    elif expected_rhs_lt_lhs and not expected_lhs_lt_rhs:
        assert sorted_pair[0] is rhs_eval
    else:
        # equal case: order is stable but both are equivalent under <
        assert not (lhs_eval < rhs_eval) and not (rhs_eval < lhs_eval)