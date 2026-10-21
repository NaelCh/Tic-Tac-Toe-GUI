"""Rules and computer opponents, independent of the desktop interface."""
import random
from dataclasses import dataclass, field
from functools import lru_cache

LINES = ((0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6))


def winning_line(board):
    return next((line for line in LINES if board[line[0]] and
                 len({board[i] for i in line}) == 1), ())


def result(board):
    line = winning_line(board)
    if line:
        return board[line[0]]
    return 'draw' if all(board) else None


@dataclass
class Match:
    board: list = field(default_factory=lambda: [''] * 9)
    turn: str = 'X'

    @property
    def outcome(self):
        return result(self.board)

    def play(self, cell):
        if not isinstance(cell, int) or not 0 <= cell < 9:
            raise ValueError('Cell must be an integer from 0 to 8')
        if self.outcome or self.board[cell]:
            return False
        self.board[cell] = self.turn
        self.turn = 'O' if self.turn == 'X' else 'X'
        return True


@lru_cache(maxsize=None)
def _value(board, turn):
    outcome = result(board)
    if outcome:
        return 0 if outcome == 'draw' else (1 if outcome == turn else -1)
    other = 'O' if turn == 'X' else 'X'
    return max(-_value(board[:i] + (turn,) + board[i+1:], other)
               for i, cell in enumerate(board) if not cell)


def best_move(board, turn):
    """Optimal legal move; prefer center, then corners on ties."""
    if result(board):
        return None
    board = tuple(board)
    other = 'O' if turn == 'X' else 'X'
    moves = [i for i in (4,0,2,6,8,1,3,5,7) if not board[i]]
    return max(moves, key=lambda i: -_value(board[:i] + (turn,) + board[i+1:], other))


def choose_move(board, turn, difficulty, rng=None):
    """Choose a legal move without changing the board.

    Medium sees immediate wins and threats. Hard adds perfect play on 85% of
    non-forced decisions, leaving occasional openings for a human to exploit.
    Neither intermediate level ever deliberately misses a one-move win/block.
    ``rng`` can be a seeded Random instance for reproducible games and tests.
    """
    if difficulty not in ('easy', 'medium', 'hard', 'unbeatable'):
        raise ValueError(f'Unknown difficulty: {difficulty}')
    if result(board):
        return None
    if difficulty == 'unbeatable':
        return best_move(board, turn)
    rng = random if rng is None else rng
    legal = [i for i, value in enumerate(board) if not value]
    if difficulty == 'easy':
        return rng.choice(legal)
    other = 'O' if turn == 'X' else 'X'
    for player in (turn, other):
        for cell in legal:
            candidate = list(board)
            candidate[cell] = player
            if result(candidate) == player:
                return cell
    if difficulty == 'hard' and rng.random() < .85:
        return best_move(board, turn)
    return rng.choice(legal)
