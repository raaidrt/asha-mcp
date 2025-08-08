from typing import Any
from mcp.server.fastmcp import FastMCP, Image

import chess
import chess.svg
from pathlib import Path

import stockfish

from PIL import Image as PILImage

import time
import os

stockfish_path = Path(__file__).parent / 'stockfish_bin'
stockfish_binary = next(stockfish_path.iterdir())

mcp = FastMCP('chess-ai')
path = str(stockfish_binary)
engine = stockfish.Stockfish(str(stockfish_binary))


def get_eval_string(eval: dict[Any, Any]) -> str:
    if eval['type'] == 'cp':
        return f'CP[{eval["value"]}]'
    return f'Mate[{eval["value"]}]'


@mcp.tool()
async def eval_next_moves(board_fen: str) -> str:
    board = chess.Board(board_fen)
    next_moves = board.generate_legal_moves()
    result: dict[str, str] = {}
    for move in next_moves:
        board.push(move)
        engine.set_fen_position(board.fen())
        engine.set_depth(10)
        result[board.fen()] = get_eval_string(engine.get_evaluation())
        board.pop()

    return str(result)


@mcp.tool()
async def get_next_board_state(board_fen: str, move_san: str) -> str:
    board = chess.Board(board_fen)
    board.push_san(move_san)
    return board.fen()


@mcp.tool()
async def get_evaluation(board_fen: str) -> str:
    board = chess.Board(board_fen)
    engine.set_fen_position(board.fen())
    return get_eval_string(engine.get_evaluation())


@mcp.tool()
async def start_board() -> str:
    return chess.Board().fen()


@mcp.tool()
async def board_image(board_fen: str) -> Image:
    svg_source = chess.svg.board(chess.Board(board_fen))
    filename = Path(f'/tmp/_asha_stockfish_{time.time()}_{os.getpid()}.svg')
    with open(filename, 'w') as f:
        f.write(svg_source)
    img = PILImage.open(filename)
    return Image(data=img.tobytes(), format='png')


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
