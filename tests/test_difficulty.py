"""Difficulty contracts: tactics, fallibility, legal moves and unchanged input."""
import random
import unittest

from engine import Match, best_move, choose_move, result


LEVELS = ('easy', 'medium', 'hard', 'unbeatable')


class ControlledRandom:
    """Select a deliberate legal mistake without probabilistic test failures."""
    def __init__(self, cell, roll=1.0):
        self.cell = cell
        self.roll = roll

    def choice(self, moves):
        if self.cell not in moves:
            raise AssertionError(f'Requested cell {self.cell} is not a candidate: {moves}')
        return self.cell

    def random(self):
        return self.roll


class DifficultyTests(unittest.TestCase):
    def test_tactical_levels_take_a_win_before_blocking(self):
        for player, other in (('X', 'O'), ('O', 'X')):
            board = [player, player, '', other, other, '', '', '', '']
            for level in ('medium', 'hard', 'unbeatable'):
                with self.subTest(player=player, level=level):
                    # The opponent also threatens a win at 5; win now at 2.
                    self.assertEqual(choose_move(board, player, level), 2)

    def test_tactical_levels_block_an_immediate_loss(self):
        for player, other in (('X', 'O'), ('O', 'X')):
            board = [other, other, '', '', player, '', '', '', '']
            for level in ('medium', 'hard', 'unbeatable'):
                with self.subTest(player=player, level=level):
                    self.assertEqual(choose_move(board, player, level), 2)

    def test_easy_can_miss_a_threat(self):
        board = ['X', 'X', '', 'O', '', '', '', '', '']
        self.assertEqual(choose_move(board, 'O', 'easy', ControlledRandom(8)), 8)

    def test_medium_and_hard_can_be_beaten_by_a_fork(self):
        for level in ('medium', 'hard'):
            with self.subTest(level=level):
                board = ['X', '', '', '', 'O', '', '', '', 'X']
                cell = choose_move(board, 'O', level, ControlledRandom(2))
                match = Match(board.copy(), 'O')
                self.assertTrue(match.play(cell))
                self.assertTrue(match.play(6))  # X now threatens both 3 and 7.
                self.assertTrue(match.play(choose_move(match.board, 'O', level)))
                winning_cell = 3 if not match.board[3] else 7
                self.assertTrue(match.play(winning_cell))
                self.assertEqual(match.outcome, 'X')

    def test_hard_usually_defends_against_the_fork(self):
        board = ['X', '', '', '', 'O', '', '', '', 'X']
        self.assertIn(choose_move(board, 'O', 'hard', ControlledRandom(2, .5)),
                      (1, 3, 5, 7))

    def test_unbeatable_ignores_random_mistakes(self):
        board = ['X', '', '', '', 'O', '', '', '', 'X']
        self.assertEqual(choose_move(board, 'O', 'unbeatable', ControlledRandom(2)),
                         best_move(board, 'O'))

    def test_finished_games_have_no_computer_move(self):
        boards = (['X', 'X', 'X', 'O', 'O', '', '', '', ''],
                  ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X'])
        for board in boards:
            for level in LEVELS:
                with self.subTest(board=board, level=level):
                    self.assertIsNone(choose_move(board, 'O', level))

    def test_unknown_difficulty_is_rejected(self):
        with self.assertRaises(ValueError):
            choose_move([''] * 9, 'X', 'impossible')

    def test_legal_moves_and_unchanged_board_in_all_reachable_positions(self):
        visited = set()
        rng = random.Random(125)

        def walk(board, turn):
            position = (tuple(board), turn)
            if position in visited or result(board):
                return
            visited.add(position)
            before = board.copy()
            for level in LEVELS:
                cell = choose_move(board, turn, level, rng)
                self.assertIn(cell, [i for i, value in enumerate(board) if not value])
                self.assertEqual(board, before)
            for cell, value in enumerate(board):
                if not value:
                    child = board.copy()
                    child[cell] = turn
                    walk(child, 'O' if turn == 'X' else 'X')

        for starter in ('X', 'O'):
            walk([''] * 9, starter)
        self.assertGreater(len(visited), 8000)


if __name__ == '__main__':
    unittest.main()
