import unittest
from engine import LINES, Match, best_move, result, winning_line


class RulesTests(unittest.TestCase):
    def test_every_winning_line_for_both_players(self):
        for player in ('X', 'O'):
            for line in LINES:
                board = [''] * 9
                for i in line:
                    board[i] = player
                self.assertEqual(result(board), player)
                self.assertEqual(winning_line(board), line)

    def test_draw(self):
        match = Match()
        for cell in (0, 1, 2, 4, 3, 5, 7, 6, 8):
            self.assertTrue(match.play(cell))
        self.assertEqual(match.outcome, 'draw')
        self.assertIsNone(best_move(match.board, match.turn))

    def test_occupied_cell_preserves_turn(self):
        match = Match()
        match.play(4)
        self.assertFalse(match.play(4))
        self.assertEqual(match.turn, 'O')
        self.assertEqual(match.board[4], 'X')

    def test_no_moves_after_win(self):
        match = Match()
        for cell in (0, 3, 1, 4, 2):
            match.play(cell)
        self.assertFalse(match.play(8))
        self.assertEqual(match.board[8], '')

    def test_invalid_coordinates(self):
        for cell in (-1, 9, '1', None):
            with self.assertRaises(ValueError):
                Match().play(cell)

    def test_independent_boards(self):
        first, second = Match(), Match()
        first.play(0)
        self.assertEqual(second.board, [''] * 9)

    def test_computer_never_loses_against_any_human_sequence(self):
        # Exhaustively branch all human choices, with computer starting or second.
        leaves = 0

        def walk(board, turn, computer):
            nonlocal leaves
            outcome = result(board)
            if outcome:
                leaves += 1
                self.assertIn(outcome, (computer, 'draw'))
                return
            other = 'O' if turn == 'X' else 'X'
            cells = ([best_move(board, turn)] if turn == computer
                     else [i for i, value in enumerate(board) if not value])
            for cell in cells:
                updated = board.copy()
                updated[cell] = turn
                walk(updated, other, computer)

        for computer in ('X', 'O'):
            walk([''] * 9, 'X', computer)
        self.assertGreater(leaves, 100)


if __name__ == '__main__':
    unittest.main()
