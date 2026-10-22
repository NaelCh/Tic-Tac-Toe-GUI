"""Integration tests: require a real or virtual X display on Linux."""
import time
import unittest
from unittest.mock import patch
from engine import Match
from game import TicTacToe, MODES


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.app = TicTacToe()
        self.app.sounds.set_enabled(False)
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

    def test_sidebar_selects_difficulty_and_remembers_it(self):
        self.app.mode_buttons[MODES[3]].invoke()
        self.assertEqual(self.app.active_mode, MODES[3])
        self.assertTrue(self.app.computer_button.selected)
        self.assertTrue(self.app.mode_buttons[MODES[3]].selected)
        self.app.local_button.invoke()
        self.assertEqual(self.app.active_mode, MODES[0])
        self.app.computer_button.invoke()
        self.assertEqual(self.app.active_mode, MODES[3])

    def test_actual_mouse_and_keyboard_input(self):
        first = self.app.buttons[0]
        first.event_generate('<Button-1>', x=30, y=30)
        self.app.update()
        self.assertEqual(self.app.match.board[0], 'X')
        first.event_generate('<Button-1>', x=30, y=30)
        self.assertEqual(self.app.match.turn, 'O')
        second = self.app.buttons[1]
        second.focus_force()
        self.app.update()
        second.event_generate('<KeyPress-space>')
        self.app.update()
        self.assertEqual(self.app.match.board[1], 'O')
        self.app.event_generate('<KeyPress-3>')
        self.app.update()
        self.assertEqual(self.app.match.board[8], 'X')

    def test_number_keys_follow_numeric_keypad_layout(self):
        self.app.focus_force()
        self.app.update()
        for prefix in ('', 'KP_'):
            for key, cell in (('7', 0), ('8', 1), ('9', 2), ('4', 3), ('5', 4),
                              ('6', 5), ('1', 6), ('2', 7), ('3', 8)):
                with self.subTest(key=prefix+key):
                    self.app._reset_session()
                    self.app.event_generate(f'<KeyPress-{prefix}{key}>', state=0x10)
                    self.app.update()
                    self.assertEqual(self.app.match.board[cell], 'X')
                    self.assertEqual(self.app.match.board.count('X'), 1)

    def test_empty_tiles_display_matching_numeric_keypad_labels(self):
        # Read the actual canvas labels, including after a resize/reset redraw.
        self.app.geometry('860x660')
        self.app.update()
        for cell, expected in enumerate(('7', '8', '9', '4', '5', '6', '1', '2', '3')):
            tile = self.app.buttons[cell]
            tile.hovered = False
            tile.draw()
            labels = [tile.itemcget(item, 'text') for item in tile.find_all()
                      if tile.type(item) == 'text']
            self.assertEqual(labels, [expected])

    def test_small_window_preserves_playable_board_and_controls(self):
        self.app.geometry('860x660')
        self.app.update()
        for widget in (*self.app.buttons.values(), self.app.next_button):
            self.assertGreater(widget.winfo_height(), 40)
            self.assertGreater(widget.winfo_width(), 40)
            self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),
                                 self.app.winfo_rooty()+self.app.winfo_height())

    def test_winning_tiles_highlight_and_reset(self):
        for cell in (0, 3, 1, 4, 2):
            self.app.buttons[cell].invoke()
        self.assertEqual([i for i, button in self.app.buttons.items() if button.winning],
                         [0, 1, 2])
        self.app.next_round()
        self.assertFalse(any(button.winning for button in self.app.buttons.values()))

    def test_help_opens_and_closes_with_escape(self):
        self.app.show_help()
        self.app.update()
        popup = next(widget for widget in self.app.winfo_children()
                     if widget.winfo_class() == 'Toplevel')
        popup.focus_force()
        self.app.update()
        popup.event_generate('<KeyPress-Escape>')
        self.app.update()
        self.assertFalse(popup.winfo_exists())

    def test_moves_and_round_end_use_distinct_sound_effects(self):
        with patch.object(self.app.sounds, 'play') as play:
            self.app.buttons[0].invoke()
            play.assert_called_once_with('move_x')
            self.app.buttons[0].invoke()
            self.assertEqual(play.call_count, 1)
            self.app.buttons[3].invoke()
            play.assert_called_with('move_o')
            for cell in (1, 4, 2):
                self.app.buttons[cell].invoke()
            play.assert_called_with('win')

    def test_action_buttons_click_and_f2_toggles_mute(self):
        with patch.object(self.app.sounds, 'play') as play:
            self.app.mode_buttons[MODES[2]].invoke()
            play.assert_called_once_with('click')
        self.app.sound_button.invoke()
        self.assertTrue(self.app.sounds.enabled)
        self.app.focus_force()
        self.app.update()
        self.app.event_generate('<KeyPress-F2>')
        self.assertFalse(self.app.sounds.enabled)
        self.assertIn('σίγαση', self.app.sound_button.text)

    def test_computer_victory_plays_loss_sound(self):
        self.app.select_mode(MODES[-1])
        self.app.match = Match(['O', 'O', '', 'X', 'X', '', '', '', ''], 'O')
        self.app._render()
        with patch.object(self.app.sounds, 'play') as play:
            self.app._computer_move()
            self.assertEqual(self.app.match.outcome, 'O')
            self.assertEqual(self.app.scores['O'], 1)
            play.assert_called_once_with('lose')

    def test_human_victory_against_computer_keeps_win_sound(self):
        self.app.select_mode(MODES[-1])
        self.app.match = Match(['X', 'X', '', 'O', 'O', '', '', '', ''], 'X')
        self.app._render()
        with patch.object(self.app.sounds, 'play') as play:
            self.app.buttons[2].invoke()
            self.assertEqual(self.app.match.outcome, 'X')
            play.assert_called_once_with('win')

    def test_local_o_victory_keeps_win_sound(self):
        with patch.object(self.app.sounds, 'play') as play:
            for cell in (0, 3, 1, 4, 8, 5):
                self.app.buttons[cell].invoke()
            self.assertEqual(self.app.match.outcome, 'O')
            play.assert_called_with('win')

    def test_draw_keeps_draw_sound(self):
        with patch.object(self.app.sounds, 'play') as play:
            for cell in (0, 1, 2, 4, 3, 5, 7, 6, 8):
                self.app.buttons[cell].invoke()
            self.assertEqual(self.app.match.outcome, 'draw')
            play.assert_called_with('draw')


if __name__ == '__main__':
    unittest.main()
