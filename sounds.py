"""Optional asynchronous audio with native OS players and no runtime packages."""
from pathlib import Path
import importlib
import shutil
import subprocess
import sys
import threading

SOUND_NAMES = frozenset(('click', 'move_x', 'move_o', 'win', 'draw'))
_STOP = object()


class SoundPlayer:
    """Play bundled WAV effects; missing audio devices never prevent playing.

    Windows uses the native winsound API. macOS/Linux use one replaceable child
    player managed by a daemon worker, so clicks never wait for audio playback.
    """
    def __init__(self, asset_dir=None):
        self.asset_dir = (Path(asset_dir) if asset_dir is not None else
                          Path(__file__).resolve().parent / 'assets' / 'sounds')
        self._enabled = True
        self._closed = False
        self._winsound = None
        self._player = None
        self._process = None
        self._thread = None
        self._condition = threading.Condition()
        self._request = None
        if sys.platform == 'win32':
            try:
                self._winsound = importlib.import_module('winsound')
            except ImportError:
                pass
        elif sys.platform == 'darwin':
            executable = shutil.which('afplay')
            if executable:
                self._player = [executable]
        elif sys.platform.startswith('linux'):
            for name in ('paplay', 'aplay'):
                executable = shutil.which(name)
                if executable:
                    self._player = [executable] + (['-q'] if name == 'aplay' else [])
                    break

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self.set_enabled(value)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if not self._enabled:
            self._stop_windows()
            with self._condition:
                self._request = _STOP
                self._condition.notify()

    def play(self, name):
        if not self._enabled or self._closed or name not in SOUND_NAMES:
            return False
        path = self.asset_dir / f'{name}.wav'
        if not path.is_file():
            return False
        if self._winsound is not None:
            try:
                flags = (self._winsound.SND_FILENAME | self._winsound.SND_ASYNC |
                         self._winsound.SND_NODEFAULT)
                self._winsound.PlaySound(str(path), flags)
                return True
            except (OSError, RuntimeError):
                return False
        if self._player is None:
            return False
        with self._condition:
            self._request = path
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, daemon=True,
                                                name='triliza-audio')
                self._thread.start()
            self._condition.notify()
        return True

    def _stop_windows(self):
        if self._winsound is not None:
            try:
                self._winsound.PlaySound(None, 0)
            except (OSError, RuntimeError):
                pass

    def _stop_process(self):
        process, self._process = self._process, None
        if process is None:
            return
        try:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=.2)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.wait(timeout=.2)
            except (OSError, subprocess.TimeoutExpired):
                pass
        except OSError:
            pass

    def _run(self):
        while True:
            with self._condition:
                if self._request is None and not self._closed:
                    self._condition.wait(timeout=.05)
                request, self._request = self._request, None
                closed = self._closed
            if request is None and not closed:
                if self._process is not None and self._process.poll() is not None:
                    self._stop_process()
                continue
            self._stop_process()
            if closed:
                return
            # Keep only the latest request if several buttons were pressed while
            # the previous player was stopping. Muting also cancels pending audio.
            with self._condition:
                if self._request is not None:
                    request, self._request = self._request, None
                if self._closed:
                    return
                if request is _STOP or not self._enabled:
                    continue
                try:
                    self._process = subprocess.Popen(
                        self._player + [str(request)], stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError:
                    self._process = None

    def close(self):
        self._closed = True
        self._stop_windows()
        with self._condition:
            self._request = _STOP
            self._condition.notify()
