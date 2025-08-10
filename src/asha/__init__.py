from typing import Any
from mcp.server.fastmcp import FastMCP

import chess
import chess.svg
from pathlib import Path

import stockfish

from cairosvg import svg2png

import time
import os

stockfish_path = Path(__file__).parent / 'stockfish_bin'
stockfish_binary = next(stockfish_path.iterdir())

mcp = FastMCP('chess-ai')
path = str(stockfish_binary)
engine = stockfish.Stockfish(str(stockfish_binary))


class Eval:
    def __init__(self, kind: str, is_white: bool, value: float):
        self.kind = kind
        self.value = value
        self.is_white = is_white

    def __repr__(self):
        if self.kind == 'cp':
            return f'CentipawnLoss[{self.value}]'
        return f'MateIn[{self.value}]'

    def __lt__(self, other: 'Eval') -> bool:
        match (self.kind, other.kind):
            case ('cp', 'cp'):
                return self.value > other.value if self.is_white else self.value < other.value
            case ('cp', 'mate'):
                return True
            case ('mate', 'cp'):
                return False
            case ('mate', 'mate'):
                return self.value < other.value if self.is_white else self.value > other.value


@mcp.tool()
async def eval_next_moves(board_fen: str, is_white: bool, cutoff: int | None) -> list[dict[str, str]]:
    board = chess.Board(board_fen)
    next_moves = board.generate_legal_moves()
    result: list[dict[str, Any]] = []
    for move in next_moves:
        board.push(move)
        engine.set_fen_position(board.fen())
        engine.set_depth(10)
        result.append({
            'eval': Eval(engine.get_evaluation()['type'], is_white, engine.get_evaluation()['value']),
            'move': str(move),
        })
        board.pop()

    sorted_result = sorted(result, key=lambda x: x['eval'])
    cutoff_value = cutoff if cutoff is not None else len(sorted_result)
    return list({"move": x['move'], "eval": str(x['eval'])} for x in sorted_result[:cutoff_value])

@mcp.tool()
async def get_next_board_state(board_fen: str, move_san: str) -> str:
    board = chess.Board(board_fen)
    board.push_san(move_san)
    return board.fen()


@mcp.tool()
async def get_evaluation(board_fen: str) -> str:
    board = chess.Board(board_fen)
    engine.set_fen_position(board.fen())
    return str(Eval(engine.get_evaluation()['type'], board.turn, engine.get_evaluation()['value']))


@mcp.tool()
async def start_board() -> str:
    return chess.Board().fen()


@mcp.tool()
async def board_image_filepath(board_fen: str) -> str:
    svg_source = chess.svg.board(chess.Board(board_fen))
    epoch_time = str(time.time())
    epoch_time = epoch_time.replace('.', '_')
    filename = f'/tmp/_asha_stockfish_{epoch_time}_{os.getpid()}'

    with open(f'{filename}.svg', 'w') as f:
        f.write(svg_source)

    svg2png(
        url=f'{filename}.svg',
        output_height=256,
        output_width=256,
        write_to=f'{filename}.png',
    )

    return f'{filename}.png'


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
