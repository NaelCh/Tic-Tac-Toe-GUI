"""Native audio routing, graceful failure and bundled sound integrity."""
from pathlib import Path
from types import SimpleNamespace
import struct
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import wave

from sounds import SOUND_NAMES, SoundPlayer


class FakeProcess:
    def __init__(self, *, stopping=None, release=None):
        self.returncode = None
        self.stopping, self.release = stopping, release
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 0
        if self.stopping:
            self.stopping.set()

    def wait(self, timeout=None):
        if self.release:
            self.release.wait(timeout=timeout)
        return self.returncode

    def kill(self):
        self.returncode = -9


class SoundTests(unittest.TestCase):
    @staticmethod
    def finish(player):
        player.close()
        if player._thread is not None:
            player._thread.join(timeout=1)
            if player._thread.is_alive():
                raise AssertionError('Audio worker did not shut down')

    def windows_player(self):
        backend = SimpleNamespace(PlaySound=Mock(), SND_FILENAME=0x20000,
                                  SND_ASYNC=1, SND_NODEFAULT=2)
        with patch('sounds.sys.platform', 'win32'), \
             patch('sounds.importlib.import_module', return_value=backend):
            player = SoundPlayer()
        self.addCleanup(self.finish, player)
        return player, backend

    def test_windows_uses_bundled_file_and_nonblocking_flags(self):
        player, backend = self.windows_player()
        self.assertTrue(player.play('move_x'))
        backend.PlaySound.assert_called_once_with(
            str(player.asset_dir/'move_x.wav'), 0x20000 | 1 | 2)

    def test_mute_stops_current_sound_and_prevents_new_audio(self):
        player, backend = self.windows_player()
        player.play('click')
        player.set_enabled(False)
        backend.PlaySound.assert_called_with(None, 0)
        backend.PlaySound.reset_mock()
        self.assertFalse(player.play('move_o'))
        backend.PlaySound.assert_not_called()
        player.enabled = True
        self.assertTrue(player.play('move_o'))

    def test_windows_device_failure_does_not_escape(self):
        player, backend = self.windows_player()
        backend.PlaySound.side_effect = RuntimeError('No audio device')
        self.assertFalse(player.play('click'))
        player.set_enabled(False)
        player.close()

    def test_invalid_missing_or_closed_sounds_are_ignored(self):
        player, backend = self.windows_player()
        self.assertFalse(player.play('../private-file'))
        with tempfile.TemporaryDirectory() as empty:
            player.asset_dir = Path(empty)
            self.assertFalse(player.play('click'))
        backend.PlaySound.assert_not_called()
        player.close()
        self.assertFalse(player.play('win'))

    def test_absent_native_player_is_silent(self):
        with patch('sounds.sys.platform', 'linux'), patch('sounds.shutil.which', return_value=None):
            player = SoundPlayer()
            self.assertFalse(player.play('click'))
            self.assertIsNone(player._thread)
            self.finish(player)

    def test_macos_and_linux_use_argument_lists_not_a_shell(self):
        for platform, executable, arguments in (
            ('darwin', 'afplay', []),
            ('linux', 'paplay', []),
            ('linux', 'aplay', ['-q']),
        ):
            with self.subTest(platform=platform, executable=executable):
                started = threading.Event()
                process = FakeProcess()
                def start(*args, **kwargs):
                    started.set()
                    return process
                with patch('sounds.sys.platform', platform), \
                     patch('sounds.shutil.which', side_effect=lambda name: '/native/'+name if name == executable else None), \
                     patch('sounds.subprocess.Popen', side_effect=start) as spawn:
                    player = SoundPlayer()
                    try:
                        self.assertTrue(player.play('click'))
                        self.assertTrue(started.wait(timeout=1))
                        spawn.assert_called_once_with(
                            ['/native/'+executable]+arguments+[str(player.asset_dir/'click.wav')],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    finally:
                        self.finish(player)
                    self.assertTrue(process.terminated)

    def test_rapid_clicks_replace_playback_and_keep_only_latest_request(self):
        first_started, stopping, release, latest_started = (threading.Event() for _ in range(4))
        first = FakeProcess(stopping=stopping, release=release)
        second = FakeProcess()
        calls = []
        def spawn(arguments, **kwargs):
            calls.append(arguments)
            if len(calls) == 1:
                first_started.set()
                return first
            latest_started.set()
            return second
        with patch('sounds.sys.platform', 'linux'), \
             patch('sounds.shutil.which', return_value='/native/paplay'), \
             patch('sounds.subprocess.Popen', side_effect=spawn):
            player = SoundPlayer()
            try:
                player.play('click')
                self.assertTrue(first_started.wait(timeout=1))
                player.play('move_x')
                self.assertTrue(stopping.wait(timeout=1))
                # play() returns even while the old audio process is stopping.
                player.play('move_o')
                self.assertFalse(release.is_set())
                release.set()
                self.assertTrue(latest_started.wait(timeout=1))
                self.assertEqual(len(calls), 2)
                self.assertTrue(calls[-1][-1].endswith('move_o.wav'))
            finally:
                release.set()
                self.finish(player)

    def test_missing_posix_executable_after_discovery_is_harmless(self):
        attempted = threading.Event()
        def missing(*args, **kwargs):
            attempted.set()
            raise FileNotFoundError('Player was removed')
        with patch('sounds.sys.platform', 'linux'), \
             patch('sounds.shutil.which', return_value='/native/paplay'), \
             patch('sounds.subprocess.Popen', side_effect=missing):
            player = SoundPlayer()
            try:
                self.assertTrue(player.play('win'))
                self.assertTrue(attempted.wait(timeout=1))
            finally:
                self.finish(player)

    def test_bundled_effects_are_short_mono_pcm_with_headroom(self):
        directory = Path(__file__).resolve().parents[1]/'assets'/'sounds'
        for name in SOUND_NAMES:
            with self.subTest(name=name), wave.open(str(directory/f'{name}.wav'), 'rb') as sound:
                self.assertEqual(sound.getnchannels(), 1)
                self.assertEqual(sound.getsampwidth(), 2)
                self.assertEqual(sound.getcomptype(), 'NONE')
                self.assertGreater(sound.getnframes()/sound.getframerate(), .02)
                self.assertLess(sound.getnframes()/sound.getframerate(), .5)
                frames = sound.readframes(sound.getnframes())
                samples = struct.unpack(f'<{len(frames)//2}h', frames)
                self.assertGreater(max(abs(value) for value in samples), 100)
                self.assertLess(max(abs(value) for value in samples), 32767*.25)

    def test_loss_effect_is_bundled_and_distinct_from_victory(self):
        directory = Path(__file__).resolve().parents[1]/'assets'/'sounds'
        self.assertIn('lose', SOUND_NAMES)
        self.assertNotEqual((directory/'lose.wav').read_bytes(), (directory/'win.wav').read_bytes())


if __name__ == '__main__':
    unittest.main()
