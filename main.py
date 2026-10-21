"""Launch the desktop game or verify a frozen installation for release builds."""
import argparse
import json
from pathlib import Path
import sys
import wave

from game import TicTacToe
from sounds import SOUND_NAMES
from version import VERSION


def smoke_test(report_path):
    app = None
    result = {'ok': False, 'frozen': bool(getattr(sys, 'frozen', False)), 'version': VERSION}
    try:
        app = TicTacToe()
        app.sounds.set_enabled(False)
        app.update()
        for cell in (0, 3, 1, 4, 2):
            app.buttons[cell].invoke()
        app.update()
        assert app.match.outcome == 'X' and app.scores['X'] == 1
        assert all(button['state'] == 'disabled' for button in app.buttons.values())
        assert sum(button.winning for button in app.buttons.values()) == 3
        app.next_round()
        assert app.match.board == [''] * 9 and app.match.turn == 'O'
        for name in SOUND_NAMES:
            with wave.open(str(app.sounds.asset_dir / f'{name}.wav'), 'rb') as sound:
                assert sound.getnframes() > 0 and sound.getnchannels() == 1
        assert 'lose' in SOUND_NAMES
        result.update(ok=True, sounds_bundled=True, loss_sound_bundled=True)
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    finally:
        if app is not None:
            app.close()
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1


def main():
    parser = argparse.ArgumentParser(description='Τρίλιζα')
    parser.add_argument('--smoke-test', action='store_true', help='Verify an installed release')
    parser.add_argument('--report', help='Path to the JSON verification report')
    args = parser.parse_args()
    if args.smoke_test:
        if not args.report:
            parser.error('--smoke-test requires --report')
        return smoke_test(args.report)
    app = TicTacToe()
    app.mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
