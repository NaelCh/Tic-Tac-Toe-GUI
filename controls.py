"""Shared board labels and numeric-keyboard input mapping."""

CELL_KEYS = ('7', '8', '9', '4', '5', '6', '1', '2', '3')
KEY_TO_CELL = {key: cell for cell, key in enumerate(CELL_KEYS)}


def cell_for_key(character, keysym=''):
    """Accept digits from the number row or a numeric keypad (Num Lock on)."""
    if character in KEY_TO_CELL:
        return KEY_TO_CELL[character]
    if keysym.startswith('KP_'):
        return KEY_TO_CELL.get(keysym[3:])
    return None
