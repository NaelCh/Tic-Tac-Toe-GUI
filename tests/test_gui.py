"""Integration tests: require a real or virtual X display on Linux."""
import time
import unittest
from unittest.mock import patch
from game import TicTacToe, MODES


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.app = TicTacToe()
        self.app.update()
        self.addCleanup(self.app.close)

    def wait_for_computer(self):
        deadline = time.monotonic() + 3
        while self.app.pending is not None and time.monotonic() < deadline:
            self.app.update()
            time.sleep(.01)
        self.assertIsNone(self.app.pending)

    def test_buttons_win_score_and_new_round(self):
        for cell in (0, 3, 1, 4, 2):
            self.app.buttons[cell].invoke()
        self.assertEqual(self.app.match.outcome, 'X')
        self.assertEqual(self.app.scores['X'], 1)
        self.assertTrue(all(str(b['state']) == 'disabled' for b in self.app.buttons.values()))
        self.app.handle_click(8)
        self.assertEqual(self.app.scores['X'], 1)
        self.app.next_round()
        self.assertEqual(self.app.match.board, [''] * 9)
        self.assertEqual(self.app.match.turn, 'O')
        self.assertEqual(self.app.scores['X'], 1)

    def test_draw_and_reset(self):
        for cell in (0, 1, 2, 4, 3, 5, 7, 6, 8):
            self.app.buttons[cell].invoke()
        self.assertEqual(self.app.scores['draw'], 1)
        with patch('game.messagebox.askyesno', return_value=True):
            self.app.reset_session()
        self.assertFalse(any(self.app.scores.values()))
        self.assertEqual(self.app.match.turn, 'X')

    def test_all_computer_levels_and_alternating_start(self):
        for mode in MODES[1:]:
            self.app.mode.set(mode)
            with patch('game.messagebox.askyesno', return_value=True):
                self.app.change_mode()
            self.app.buttons[0].invoke()
            self.assertIsNotNone(self.app.pending)
            self.app.handle_click(1)  # Human cannot play during computer delay.
            self.assertEqual(sum(bool(v) for v in self.app.match.board), 1)
            self.wait_for_computer()
            self.assertEqual(self.app.match.board.count('O'), 1)
            with patch('game.messagebox.askyesno', return_value=True):
                self.app.next_round()
            self.wait_for_computer()
            self.assertEqual(self.app.match.board.count('O'), 1)
            self.assertEqual(self.app.match.turn, 'X')

    def test_mode_cancel_preserves_round(self):
        self.app.handle_click(0)
        self.app.mode.set(MODES[-1])
        with patch('game.messagebox.askyesno', return_value=False):
            self.app.change_mode()
        self.assertEqual(self.app.mode.get(), MODES[0])
        self.assertEqual(self.app.match.board[0], 'X')

    def test_reset_cancels_pending_computer_callback(self):
        self.app.mode.set(MODES[-1])
        self.app.change_mode()
        self.app.handle_click(0)
        with patch('game.messagebox.askyesno', return_value=True):
            self.app.reset_session()
        self.assertIsNone(self.app.pending)
        self.app.after(500, self.app.quit)
        self.app.mainloop()
        self.assertEqual(self.app.match.board, [''] * 9)

    def test_cancel_mode_change_during_computer_move(self):
        self.app.mode.set(MODES[-1])
        self.app.change_mode()
        self.app.handle_click(0)
        self.app.mode.set(MODES[0])

        def cancel_after_computer_moves(*args, **kwargs):
            # A real modal dialog keeps processing scheduled Tk callbacks.
            self.wait_for_computer()
            return False

        with patch('game.messagebox.askyesno', side_effect=cancel_after_computer_moves):
            self.app.change_mode()
        self.assertEqual(self.app.mode.get(), MODES[-1])
        self.assertEqual(self.app.match.board.count('O'), 1)
        self.assertEqual(self.app.match.turn, 'X')
        self.assertIsNone(self.app.pending)
        self.assertTrue(any(str(b['state']) == 'normal' for b in self.app.buttons.values()))


if __name__ == '__main__':
    unittest.main()
