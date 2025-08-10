import sys
import types
import ast
from pathlib import Path

from PIL import Image as PILImage

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
            self.depth = None
            self.last_fen = None

        def set_fen_position(self, fen: str):
            self.last_fen = fen

        def set_depth(self, depth: int):
            self.depth = depth

        def get_evaluation(self):
            # Always return a stable evaluation for deterministic tests
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

    # Import after installing fake stockfish and creating dummy bin
    asha = importlib.import_module('asha')
    return asha


@pytest.mark.asyncio
async def test_start_board(asha_module):
    start_fen = await asha_module.start_board()
    assert start_fen == asha_module.chess.Board().fen()


@pytest.mark.asyncio
async def test_get_next_board_state(asha_module):
    board = asha_module.chess.Board()
    before_fen = board.fen()
    expected_board = asha_module.chess.Board()
    expected_board.push_san('e4')
    expected_fen = expected_board.fen()

    next_fen = await asha_module.get_next_board_state(before_fen, 'e4')
    assert next_fen == expected_fen


@pytest.mark.asyncio
async def test_get_evaluation_uses_engine(asha_module):
    # Our fake engine always returns cp 0
    fen = asha_module.chess.Board().fen()
    result = await asha_module.get_evaluation(fen)
    assert result == 'CentipawnLoss[0]'


@pytest.mark.asyncio
async def test_eval_next_moves_returns_list_of_dicts(asha_module):
    # The tool now returns a Python list of dicts with keys: 'eval', 'move', 'board'
    start_fen = asha_module.chess.Board().fen()

    result_list = await asha_module.eval_next_moves(start_fen, True, None)

    # Count legal moves from start position
    board = asha_module.chess.Board(start_fen)
    legal_moves = list(board.generate_legal_moves())

    assert isinstance(result_list, list)
    assert len(result_list) == len(legal_moves)
    assert all(isinstance(item, dict) for item in result_list)
    assert all({'move', 'board', 'eval'}.issubset(item.keys()) for item in result_list)

    # All evaluations should stringify to the stable fake "CentipawnLoss[0]"
    assert {str(item['eval']) for item in result_list} == {'CentipawnLoss[0]'}

    # Cutoff behavior should limit the number of entries
    result_cutoff = await asha_module.eval_next_moves(start_fen, True, 5)
    assert isinstance(result_cutoff, list)
    assert len(result_cutoff) == 5


@pytest.mark.asyncio
async def test_board_image_filepath(asha_module):
    fen = asha_module.chess.Board().fen()
    img_filepath = await asha_module.board_image_filepath(fen)
    assert Path(img_filepath).exists()
    img = PILImage.open(img_filepath)
    assert img.size == (256, 256)
    assert img.format == 'PNG'
