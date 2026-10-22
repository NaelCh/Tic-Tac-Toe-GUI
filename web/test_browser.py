"""Exercise the built PWA in a real browser, including a project URL and offline use.

Run ``node web/build.mjs`` first, then ``python3 web/test_browser.py``.
Requires Python Playwright and a Chromium/Chrome binary. CHROMIUM_PATH and
TRILIZA_WEB_DIR can override the browser and the production build directory.
These checks emulate phone viewports; they do not prove installation on a
physical Android device or iPhone.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
import unittest

from playwright.sync_api import expect, sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        '.webmanifest': 'application/manifest+json',
        '.js': 'text/javascript',
    }

    def log_message(self, format, *args):
        pass

    def end_headers(self):
        if self.path.startswith('/release-'):
            # Published static hosts cache assets; a new worker must bypass
            # the HTTP cache when populating its next release's shell.
            policy = 'no-cache' if self.path.endswith('/sw.js') else 'public, max-age=3600'
            self.send_header('Cache-Control', policy)
        super().end_headers()


class MobileBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        production = Path(os.environ.get('TRILIZA_WEB_DIR', root / 'dist-mobile')).resolve()
        if not (production / 'index.html').is_file():
            raise RuntimeError('Production PWA is missing; run node web/build.mjs first')
        executable = (os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
                      or shutil.which('google-chrome') or shutil.which('chromium-browser'))
        if not executable:
            raise RuntimeError('Chromium is required; set CHROMIUM_PATH to its executable')
        cls.production = production

        cls.directory = tempfile.TemporaryDirectory(prefix='triliza-mobile-browser-')
        cls.addClassCleanup(cls.directory.cleanup)
        # A project prefix matches https://owner.github.io/Tic-Tac-Toe-GUI/.
        Path(cls.directory.name, 'Tic-Tac-Toe-GUI').symlink_to(production, target_is_directory=True)
        cls.server = ThreadingHTTPServer(
            ('127.0.0.1', 0), partial(QuietHandler, directory=cls.directory.name))
        cls.server.daemon_threads = True
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.addClassCleanup(cls.stop_server)
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/Tic-Tac-Toe-GUI/'
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = cls.playwright.chromium.launch(
            executable_path=executable, headless=True, args=['--no-sandbox'])
        cls.addClassCleanup(cls.browser.close)

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=3)

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={'width': 390, 'height': 844}, is_mobile=True,
            has_touch=True, service_workers='allow')
        self.page = self.context.new_page()
        self.page_errors = []
        self.page.on('pageerror', lambda error: self.page_errors.append(str(error)))
        self.page.goto(self.url, wait_until='domcontentloaded')
        self.ready()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.page_errors, [], 'Unhandled browser errors')

    def ready(self):
        expect(self.page.locator('#board button[data-cell]')).to_have_count(9)
        expect(self.page.locator('#status')).not_to_be_empty()

    def cell(self, index):
        return self.page.locator(f'#board button[data-cell="{index}"]')

    def friend(self):
        self.page.locator('[data-opponent="friend"]').tap()
        self.selected('[data-opponent="friend"]')

    def selected(self, selector):
        self.page.wait_for_function(
            "selector => { const button = document.querySelector(selector); "
            "return button && (button.getAttribute('aria-pressed') === 'true' "
            "|| button.classList.contains('selected')); }", arg=selector)

    def test_phone_sizes_and_visible_keypad_labels(self):
        for width, height in ((390, 844), (320, 568), (812, 375)):
            with self.subTest(width=width, height=height):
                self.page.set_viewport_size({'width': width, 'height': height})
                self.page.wait_for_function(
                    'document.documentElement.scrollWidth <= window.innerWidth + 1')
                for index, label in enumerate(('7', '8', '9', '4', '5', '6', '1', '2', '3')):
                    expect(self.cell(index)).to_contain_text(label)
                    bounds = self.cell(index).bounding_box()
                    self.assertIsNotNone(bounds)
                    self.assertGreaterEqual(bounds['width'], 44)
                    self.assertGreaterEqual(bounds['height'], 44)

    def test_touch_game_win_score_and_next_round(self):
        self.friend()
        for index in (0, 3, 1, 4, 2):
            self.cell(index).tap()
        expect(self.page.locator('#score-x')).to_have_text('1')
        expect(self.page.locator('#board button:disabled')).to_have_count(9)
        expect(self.page.locator('#board button[data-symbol="X"]')).to_have_count(3)
        self.page.locator('#next-round').tap()
        expect(self.page.locator('#board button:disabled')).to_have_count(0)
        expect(self.page.locator('#score-x')).to_have_text('1')
        self.cell(0).tap()
        expect(self.cell(0)).to_have_attribute('data-symbol', 'O')

    def test_all_number_keys_follow_the_laptop_keypad(self):
        self.friend()
        for key, index in (('7', 0), ('8', 1), ('9', 2), ('4', 3), ('5', 4),
                            ('6', 5), ('1', 6), ('2', 7), ('3', 8)):
            with self.subTest(key=key):
                self.page.reload(wait_until='domcontentloaded')
                self.ready()
                self.page.keyboard.press(key)
                expect(self.cell(index)).to_have_attribute('data-symbol', 'X')
                expect(self.page.locator('#board button[data-symbol="X"]')).to_have_count(1)

    def test_computer_answers_a_touch_move(self):
        self.page.locator('[data-level="hard"]').tap()
        self.selected('[data-level="hard"]')
        self.cell(0).tap()
        expect(self.cell(0)).to_have_attribute('data-symbol', 'X')
        expect(self.page.locator('#board button[data-symbol="O"]')).to_have_count(1, timeout=6000)
        expect(self.page.locator('#board button:disabled')).to_have_count(2)
        expect(self.page.locator('#score-o')).to_have_text('0')

    def test_sound_and_difficulty_survive_reload(self):
        self.page.locator('#sound-toggle').tap()
        expect(self.page.locator('#sound-toggle')).to_have_attribute('aria-pressed', 'false')
        self.page.locator('[data-level="hard"]').tap()
        self.page.reload(wait_until='domcontentloaded')
        self.ready()
        expect(self.page.locator('#sound-toggle')).to_have_attribute('aria-pressed', 'false')
        self.selected('[data-level="hard"]')

    def test_installation_and_help_instructions_open(self):
        self.page.locator('#install-help').tap()
        dialog = self.page.locator('#install-dialog')
        expect(dialog).to_be_visible()
        expect(dialog).to_contain_text('Android')
        expect(dialog).to_contain_text('iPhone')
        dialog.locator('[data-close]').first.tap()
        expect(dialog).not_to_be_visible()
        self.page.locator('#help-button').tap()
        expect(self.page.locator('#help-dialog')).to_be_visible()
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#help-dialog')).not_to_be_visible()

    def test_cached_app_reloads_and_plays_offline(self):
        self.friend()
        self.page.evaluate('async () => { await navigator.serviceWorker.ready; }')
        self.page.wait_for_function('navigator.serviceWorker.controller !== null', timeout=20000)
        self.assertTrue(self.page.evaluate('async () => (await caches.keys()).length > 0'))
        online_color = self.page.locator('body').evaluate('element => getComputedStyle(element).backgroundColor')
        self.context.set_offline(True)
        self.page.reload(wait_until='domcontentloaded')
        self.ready()
        self.assertEqual(
            self.page.locator('body').evaluate('element => getComputedStyle(element).backgroundColor'),
            online_color)
        for index in (0, 3, 1, 4, 2):
            self.cell(index).tap()
        expect(self.page.locator('#score-x')).to_have_text('1')
        expect(self.page.locator('#board button:disabled')).to_have_count(9)

    def test_update_preserves_a_consistent_shell_until_accepted(self):
        # Two copies of the real build expose HTML/runtime version mismatches.
        # No application source or shared production build is changed.
        with tempfile.TemporaryDirectory(prefix='release-', dir=self.directory.name) as fixture:
            fixture = Path(fixture)
            shutil.copytree(self.production, fixture, dirs_exist_ok=True)
            html = (fixture / 'index.html').read_text(encoding='utf-8')
            script = (fixture / 'app.js').read_text(encoding='utf-8')
            worker = (fixture / 'sw.js').read_text(encoding='utf-8')

            def publish(version):
                (fixture / 'index.html').write_text(html.replace(
                    '</head>', f'<meta name="test-shell-version" content="{version}"></head>'),
                    encoding='utf-8')
                (fixture / 'app.js').write_text(script +
                    f'\ndocument.documentElement.dataset.testRuntimeVersion = "{version}";\n',
                    encoding='utf-8')
                updated_worker, count = re.subn(
                    r"const CACHE = CACHE_PREFIX \+ '[^']+';",
                    f"const CACHE = CACHE_PREFIX + 'browser-test-{version}';", worker)
                self.assertEqual(count, 1, 'Built worker must declare one versioned cache')
                (fixture / 'sw.js').write_text(updated_worker, encoding='utf-8')
                # SimpleHTTPRequestHandler uses one-second Last-Modified precision.
                # Ensure an immediate second release cannot be answered with 304.
                modified = time.time() + (2 if version == 'one' else 4)
                for filename in ('index.html', 'app.js', 'sw.js'):
                    os.utime(fixture / filename, (modified, modified))

            def shell_is(version):
                expect(self.page.locator('meta[name="test-shell-version"]')).to_have_attribute(
                    'content', version)
                expect(self.page.locator('html')).to_have_attribute('data-test-runtime-version', version)

            publish('one')
            self.page.goto(self.url.replace('/Tic-Tac-Toe-GUI/', f'/{fixture.name}/'),
                           wait_until='domcontentloaded')
            self.ready()
            self.page.evaluate('async () => { await navigator.serviceWorker.ready; }')
            self.page.wait_for_function('navigator.serviceWorker.controller !== null', timeout=20000)
            shell_is('one')

            publish('two')
            self.page.evaluate('async () => { '
                'const registration = await navigator.serviceWorker.getRegistration(); '
                'await registration.update(); }')
            expect(self.page.locator('#update-banner')).to_be_visible(timeout=20000)
            self.page.reload(wait_until='domcontentloaded')
            self.ready()
            shell_is('one')
            expect(self.page.locator('#update-banner')).to_be_visible()

            self.cell(0).tap()
            self.page.locator('#update-button').tap()
            expect(self.page.locator('#confirm-dialog')).to_be_visible()
            self.page.keyboard.press('Escape')
            expect(self.page.locator('[data-symbol="O"]')).to_have_count(1)
            shell_is('one')
            self.page.locator('#update-button').tap()
            self.page.locator('#confirm-dialog [value="confirm"]').tap()
            shell_is('two')
            self.ready()
            expect(self.page.locator('#board button[data-symbol]')).to_have_count(0)

            self.context.set_offline(True)
            self.page.reload(wait_until='domcontentloaded')
            self.ready()
            shell_is('two')
            self.cell(0).tap()
            expect(self.cell(0)).to_have_attribute('data-symbol', 'X')
            expect(self.page.locator('[data-symbol="O"]')).to_have_count(1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
