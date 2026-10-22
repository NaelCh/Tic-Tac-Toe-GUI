import { chooseMove, outcome, winningLine } from './engine.js';

const $ = selector => document.querySelector(selector);
const LEVELS = ['easy', 'medium', 'hard', 'unbeatable'];
const KEYS = ['7', '8', '9', '4', '5', '6', '1', '2', '3'];
const POSITIONS = ['πάνω αριστερά','πάνω κέντρο','πάνω δεξιά','μέση αριστερά','κέντρο','μέση δεξιά','κάτω αριστερά','κάτω κέντρο','κάτω δεξιά'];
const DESCRIPTIONS = {
  friend: 'Μοιραστείτε το ίδιο ταμπλό, στην ίδια συσκευή.',
  easy: 'Για μια χαλαρή αρχή. Τυχαίες κινήσεις.',
  medium: 'Λίγη σκέψη, αρκετές ευκαιρίες.',
  hard: 'Μια καλή πρόκληση. Στήσε την παγίδα σου.',
  unbeatable: 'Η απόλυτη δοκιμασία. Παίξε τέλεια για ισοπαλία.',
};
const STORAGE_KEY = 'triliza.mobile.settings.v1';
function readSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return { mode: saved.mode === 'friend' || LEVELS.includes(saved.mode) ? saved.mode : 'medium', sound: saved.sound !== false };
  } catch { return { mode: 'medium', sound: true }; }
}
const settings = readSettings();
const state = {
  mode: settings.mode, lastLevel: LEVELS.includes(settings.mode) ? settings.mode : 'medium',
  board: Array(9).fill(''), turn: 'X', starter: 'X', round: 1,
  scores: {X: 0, O: 0, draw: 0}, pending: null,
};

class AudioEffects {
  constructor(enabled) { this.enabled = enabled; this.context = null; this.buffers = new Map(); }
  unlock() {
    if (!this.enabled) return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    try {
      if (!this.context) {
        this.context = new AudioContext();
        for (const name of ['click','move_x','move_o','win','lose','draw']) {
          fetch(new URL(`./sounds/${name}.wav`, import.meta.url))
            .then(response => { if (!response.ok) throw new Error('Audio unavailable'); return response.arrayBuffer(); })
            .then(data => this.context.decodeAudioData(data))
            .then(buffer => this.buffers.set(name, buffer)).catch(() => {});
        }
      }
      if (this.context.state === 'suspended') this.context.resume().catch(() => {});
    } catch { /* Audio support never blocks play. */ }
  }
  play(name) {
    if (!this.enabled) return;
    this.unlock();
    if (!this.context) return;
    try {
      if (this.source) { try { this.source.stop(); } catch {} this.source = null; }
      const buffer = this.buffers.get(name);
      if (buffer) {
        const source = this.context.createBufferSource();
        source.buffer = buffer;
        source.connect(this.context.destination);
        source.start();
        this.source = source;
      } else {
        // A subtle fallback covers the very first tap while WAVs are decoding.
        const oscillator = this.context.createOscillator();
        const gain = this.context.createGain();
        const now = this.context.currentTime;
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(name === 'move_o' ? 510 : name === 'lose' ? 330 : 720, now);
        oscillator.frequency.exponentialRampToValueAtTime(name === 'lose' ? 220 : 520, now+.07);
        gain.gain.setValueAtTime(.0001, now);
        gain.gain.exponentialRampToValueAtTime(.08, now+.008);
        gain.gain.exponentialRampToValueAtTime(.0001, now+.09);
        oscillator.connect(gain).connect(this.context.destination);
        oscillator.start(); oscillator.stop(now+.1); this.source = oscillator;
      }
    } catch { /* Missing output device is harmless. */ }
  }
  toggle() {
    this.enabled = !this.enabled;
    if (!this.enabled && this.source) { try { this.source.stop(); } catch {} }
    if (this.enabled) this.play('click');
  }
}
const audio = new AudioEffects(settings.sound);
function saveSettings() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({mode: state.mode, sound: audio.enabled})); } catch {}
}
const isComputer = () => state.mode !== 'friend';
const computerTurn = () => isComputer() && state.turn === 'O';
const cells = [...document.querySelectorAll('[data-cell]')];
const xSvg = '<svg class="mark x" viewBox="0 0 100 100" aria-hidden="true"><line x1="22" y1="22" x2="78" y2="78"/><line x1="78" y1="22" x2="22" y2="78"/></svg>';
const oSvg = '<svg class="mark o" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="31"/></svg>';
function render() {
  const result = outcome(state.board);
  const line = winningLine(state.board);
  cells.forEach((button, index) => {
    const symbol = state.board[index];
    const previous = button.dataset.symbol || '';
    if (previous !== symbol) {
      if (symbol) {
        button.dataset.symbol = symbol;
        button.innerHTML = symbol === 'X' ? xSvg : oSvg;
      } else {
        delete button.dataset.symbol;
        button.innerHTML = '';
      }
    }
    button.classList.toggle('winning', line.includes(index));
    button.disabled = Boolean(symbol || result || computerTurn());
    button.setAttribute('aria-label', `${POSITIONS[index]}, ${symbol || 'κενό'}`);
  });
  $('#name-x').textContent = isComputer() ? 'Εσύ · X' : 'Παίκτης X';
  $('#name-o').textContent = isComputer() ? 'Υπολογιστής · O' : 'Παίκτης O';
  for (const key of ['X','O','draw']) $(`#score-${key.toLowerCase()}`).textContent = state.scores[key];
  $('#round-label').textContent = `ΓΥΡΟΣ ${String(state.round).padStart(2,'0')}`;
  $('[data-opponent="friend"]').setAttribute('aria-pressed', String(!isComputer()));
  $('[data-opponent="computer"]').setAttribute('aria-pressed', String(isComputer()));
  for (const button of document.querySelectorAll('[data-level]')) {
    button.setAttribute('aria-pressed', String(button.dataset.level === state.mode));
    button.disabled = !isComputer();
  }
  $('#mode-description').textContent = DESCRIPTIONS[state.mode];
  $('#sound-toggle').setAttribute('aria-pressed', String(audio.enabled));
  $('#sound-toggle').setAttribute('aria-label', audio.enabled ? 'Σίγαση ήχου' : 'Ενεργοποίηση ήχου');
  $('#sound-toggle').title = audio.enabled ? 'Ήχος ενεργός' : 'Σίγαση';
  if (result === 'draw') {
    $('#status').textContent = 'Στα ίσα. Άλλη μία;';
    $('#status-detail').textContent = 'Καλή αναμέτρηση. Ο επόμενος γύρος σας περιμένει.';
  } else if (result) {
    $('#status').textContent = isComputer() ? (result === 'X' ? 'Τα κατάφερες!' : 'Νίκη του υπολογιστή.') : `Νίκη για τον ${result}!`;
    $('#status-detail').textContent = 'Τρία στη σειρά. Ώρα για τη ρεβάνς!';
  } else {
    $('#status').textContent = computerTurn() ? 'Ο υπολογιστής σκέφτεται…' : isComputer() ? 'Η σειρά σου.' : `Η σειρά του ${state.turn}.`;
    $('#status-detail').textContent = computerTurn() ? 'Παρατήρησε, σχεδίασε, παίξε.' : 'Πάτησε ένα κελί και φτιάξε τη δική σου τριάδα.';
  }
}
function cancelComputer() { clearTimeout(state.pending); state.pending = null; }
function scheduleComputer() {
  if (computerTurn() && !outcome(state.board) && state.pending === null) {
    state.pending = setTimeout(() => {
      state.pending = null;
      if (!computerTurn() || outcome(state.board)) return;
      play(chooseMove(state.board, 'O', state.mode));
    }, 420);
  }
}
function play(cell) {
  if (!Number.isInteger(cell) || cell < 0 || cell > 8 || state.board[cell] || outcome(state.board)) return;
  const symbol = state.turn;
  state.board[cell] = symbol;
  const result = outcome(state.board);
  if (result) state.scores[result]++;
  state.turn = symbol === 'X' ? 'O' : 'X';
  audio.play(result === 'draw' ? 'draw' : result ? (isComputer() && result === 'O' ? 'lose' : 'win') : symbol === 'X' ? 'move_x' : 'move_o');
  render(); scheduleComputer();
}
function humanMove(cell) { if (!computerTurn()) play(cell); }
function newBoard() {
  cancelComputer(); state.board = Array(9).fill(''); state.turn = state.starter;
  render(); scheduleComputer();
}
function resetSession() {
  state.scores = {X: 0, O: 0, draw: 0}; state.round = 1; state.starter = 'X'; newBoard();
}
const dirty = () => state.board.some(Boolean) || Object.values(state.scores).some(Boolean);
function ask(message) {
  const dialog = $('#confirm-dialog');
  if (dialog.open) return Promise.resolve(false);
  const resume = state.pending !== null;
  cancelComputer();
  $('#confirm-message').textContent = message;
  dialog.returnValue = 'cancel';
  return new Promise(resolve => {
    dialog.addEventListener('close', () => {
      const accepted = dialog.returnValue === 'confirm';
      if (!accepted && resume) scheduleComputer();
      resolve(accepted);
    }, {once: true});
    dialog.showModal();
  });
}
async function changeMode(mode) {
  if (mode === state.mode) return;
  if (dirty() && !await ask('Η αλλαγή αντιπάλου μηδενίζει τον γύρο και τα σκορ. Να συνεχίσουμε;')) return;
  cancelComputer(); state.mode = mode;
  if (mode !== 'friend') state.lastLevel = mode;
  saveSettings(); resetSession();
}
async function nextRound() {
  if (state.board.some(Boolean) && !outcome(state.board) && !await ask('Να εγκαταλειφθεί ο τρέχων γύρος και να αρχίσει ο επόμενος;')) return;
  state.round++; state.starter = state.starter === 'X' ? 'O' : 'X'; newBoard();
}
function click(handler) { return event => { audio.play('click'); handler(event); }; }
for (const button of cells) button.addEventListener('click', () => humanMove(Number(button.dataset.cell)));
for (const button of document.querySelectorAll('[data-level]')) button.addEventListener('click', click(() => changeMode(button.dataset.level)));
$('[data-opponent="friend"]').addEventListener('click', click(() => changeMode('friend')));
$('[data-opponent="computer"]').addEventListener('click', click(() => changeMode(state.lastLevel)));
$('#next-round').addEventListener('click', click(nextRound));
$('#reset-score').addEventListener('click', click(async () => {
  if (!dirty() || await ask('Να μηδενιστούν τα σκορ και να ξεκινήσει νέο παιχνίδι;')) resetSession();
}));
$('#sound-toggle').addEventListener('click', () => { audio.toggle(); saveSettings(); render(); });
$('#help-button').addEventListener('click', click(() => $('#help-dialog').showModal()));
$('#install-help').addEventListener('click', click(() => $('#install-dialog').showModal()));
for (const button of document.querySelectorAll('[data-close]')) button.addEventListener('click', click(() => button.closest('dialog').close()));
document.addEventListener('keydown', event => {
  if (document.querySelector('dialog[open]') || event.ctrlKey || event.metaKey || event.altKey) return;
  const cell = KEYS.indexOf(event.key);
  if (cell !== -1) { event.preventDefault(); humanMove(cell); }
});

let installPrompt = null;
window.addEventListener('beforeinstallprompt', event => { event.preventDefault(); installPrompt = event; });
$('#install-button').addEventListener('click', click(async () => {
  if (installPrompt) {
    const prompt = installPrompt; installPrompt = null;
    try { await prompt.prompt(); await prompt.userChoice; } catch { $('#install-dialog').showModal(); }
  } else $('#install-dialog').showModal();
}));
function installed() { return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true; }
function updateInstallCard() { if (installed()) $('.install-card').hidden = true; }
window.addEventListener('appinstalled', updateInstallCard); updateInstallCard();
let waitingWorker = null;
let reloadOnControllerChange = false;
function showUpdate(worker) { waitingWorker = worker; $('#update-banner').hidden = false; }
$('#update-button').addEventListener('click', click(async () => {
  if (state.board.some(Boolean) && !outcome(state.board) && !await ask('Η ανανέωση θα ξεκινήσει νέο παιχνίδι. Συνέχεια;')) return;
  reloadOnControllerChange = true;
  waitingWorker?.postMessage('SKIP_WAITING');
}));
function connectionStatus() {
  $('#connection-status').textContent = navigator.onLine ? 'Έτοιμο για offline' : 'Χωρίς σύνδεση · παίζεις κανονικά';
}
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register(new URL('./sw.js', import.meta.url), {scope: './'})
    .then(registration => {
      if (registration.waiting) showUpdate(registration.waiting);
      registration.addEventListener('updatefound', () => {
        const worker = registration.installing;
        worker?.addEventListener('statechange', () => {
          if (worker.state === 'installed' && navigator.serviceWorker.controller) showUpdate(worker);
        });
      });
      return navigator.serviceWorker.ready;
    }).then(() => {
      connectionStatus(); window.addEventListener('online', connectionStatus); window.addEventListener('offline', connectionStatus);
    }).catch(() => { $('#connection-status').textContent = 'Παίζεις από τον browser'; });
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (reloadOnControllerChange) location.reload(); });
}
window.addEventListener('pagehide', cancelComputer);
window.addEventListener('pageshow', () => scheduleComputer());
render();
