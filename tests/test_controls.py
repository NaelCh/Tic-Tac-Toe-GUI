"""Numeric keypad input works for both OS digit events and explicit KP events."""
import unittest

from controls import cell_for_key


class KeypadTests(unittest.TestCase):
    def test_windows_native_keypad_codes_without_text(self):
        for key, cell in (('7', 0), ('8', 1), ('9', 2), ('4', 3), ('5', 4),
                          ('6', 5), ('1', 6), ('2', 7), ('3', 8)):
            with self.subTest(key=key):
                code = 0x60+int(key)
                self.assertEqual(cell_for_key('', '??', code, 'win32'), cell)
                self.assertIsNone(cell_for_key('', '', code, 'linux'))
        for code in (0x60, 0x6E, 0x24):
            self.assertIsNone(cell_for_key('', '', code, 'win32'))

    def test_keypad_digit_events(self):
        for key, cell in (('7', 0), ('8', 1), ('9', 2), ('4', 3), ('5', 4),
                          ('6', 5), ('1', 6), ('2', 7), ('3', 8)):
            with self.subTest(key=key):
                self.assertEqual(cell_for_key(key, f'KP_{key}'), cell)
                self.assertEqual(cell_for_key('', f'KP_{key}'), cell)

    def test_unrelated_keys_do_not_play_a_cell(self):
        for character, keysym in (('', ''), ('0', 'KP_0'), ('.', 'KP_Decimal'),
                                  ('', 'KP_Home'), ('', 'Home'), ('', 'F2'),
                                  ('', 'Up'), ('a', 'a')):
            with self.subTest(keysym=keysym):
                self.assertIsNone(cell_for_key(character, keysym))
