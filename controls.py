"""Shared board labels and numeric-keyboard input mapping."""
import sys

CELL_KEYS = ('7', '8', '9', '4', '5', '6', '1', '2', '3')
KEY_TO_CELL = {key: cell for cell, key in enumerate(CELL_KEYS)}


def cell_for_key(character, keysym='', keycode=None, platform=None):
    """Accept digits from the number row or a numeric keypad (Num Lock on)."""
    if character in KEY_TO_CELL:
        return KEY_TO_CELL[character]
    if keysym.startswith('KP_'):
        cell = KEY_TO_CELL.get(keysym[3:])
        if cell is not None:
            return cell
    # Windows reports numeric-pad keys as native VK_NUMPAD1..VK_NUMPAD9.
    # Keep this platform-specific: the same keycodes mean other keys on X11.
    platform = sys.platform if platform is None else platform
    if platform == 'win32' and isinstance(keycode, int) and 0x61 <= keycode <= 0x69:
        return KEY_TO_CELL[str(keycode-0x60)]
    return None
