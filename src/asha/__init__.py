from mcp.server.fastmcp import FastMCP

import chess
from pathlib import Path

import stockfish

stockfish_path = Path(__file__).parent / 'stockfish_bin'
stockfish_binary = next(stockfish_path.iterdir())

mcp = FastMCP('chess-ai')
path = str(stockfish_binary)
engine = stockfish.Stockfish(str(stockfish_binary))


@mcp.tool()
async def eval_next_moves(board_fen: str) -> str:
    board = chess.Board(board_fen)
    next_moves = board.generate_legal_moves()
    result = {}
    for move in next_moves:
        board.push(move)
        engine.set_fen_position(board.fen())
        engine.set_depth(10)
        result[board.fen()] = engine.get_evaluation() / 100
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
    return str(engine.get_evaluation() / 100)


@mcp.tool()
async def start_board() -> str:
    return chess.Board().fen()


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
