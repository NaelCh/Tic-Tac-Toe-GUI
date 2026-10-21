"""Greek desktop Tic Tac Toe with a custom, dependency-free interface."""
import sys
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont, messagebox

from engine import Match, choose_move, winning_line
from sounds import SoundPlayer
from version import VERSION
from ui import ActionButton, BoardCell, ScoreCard, rounded, BG, PANEL, TEXT, MUTED, TEAL, CORAL, PURPLE

MODES = ('Δύο παίκτες', 'Υπολογιστής · εύκολο', 'Υπολογιστής · μέτριο',
         'Υπολογιστής · δύσκολο', 'Υπολογιστής · αήττητο')
DIFFICULTIES = dict(zip(MODES[1:], ('easy', 'medium', 'hard', 'unbeatable')))
DETAILS = (
    'Μοιραστείτε το ίδιο ταμπλό.\nΟ επόμενος γύρος αλλάζει τον πρώτο παίκτη.',
    'Για μια χαλαρή αρχή.\nΟ υπολογιστής παίζει τυχαία.',
    'Λίγη σκέψη, αρκετές ευκαιρίες.\nΒλέπει απειλές, αλλά του ξεφεύγουν μερικές.',
    'Μια καλή πρόκληση, με περιθώρια νίκης.\nΣτήσε την παγίδα σου και περίμενε την ευκαιρία.',
    'Η απόλυτη δοκιμασία.\nΠαίξε τέλεια για να πετύχεις ισοπαλία.',
)


class TicTacToe(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Τρίλιζα | Μια κίνηση ακόμα')
        height = min(800, max(660, self.winfo_screenheight()-70))
        self.geometry(f'1040x{height}')
        self.minsize(860, 660)
        self.configure(bg=BG)
        self.sounds = SoundPlayer()
        if sys.platform == 'win32':
            try:
                self.iconbitmap(str(Path(__file__).resolve().parent / 'assets' / 'app.ico'))
            except tk.TclError:
                pass
        families = set(tkfont.families(self))
        candidates = ('Segoe UI', 'Helvetica Neue', 'DejaVu Sans')
        self.family = next((name for name in candidates if name in families), 'TkDefaultFont')
        self.match = Match()
        self.scores = {'X': 0, 'O': 0, 'draw': 0}
        self.round_number, self.starter, self.pending = 1, 'X', None
        self.mode = tk.StringVar(value=MODES[0])
        self.active_mode, self.last_computer_mode = MODES[0], MODES[2]
        self.status, self.subtitle, self.detail = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.round_text = tk.StringVar()
        self.buttons, self.score_cards, self.mode_buttons = {}, {}, {}
        self._build_ui()
        self._render()
        self.bind('<Control-n>', lambda event: self._shortcut(self.next_round))
        if sys.platform == 'darwin':
            self.bind('<Command-n>', lambda event: self._shortcut(self.next_round))
        self.bind('<F1>', lambda event: self._shortcut(self.show_help))
        self.bind('<F2>', lambda event: self.toggle_sound())
        self.bind('<KeyPress>', self._key_move)
        self.protocol('WM_DELETE_WINDOW', self.close)

    def label(self, parent, text=None, *, size=11, color=TEXT, bold=False,
              background=BG, **kwargs):
        return tk.Label(parent, text=text, bg=background, fg=color,
                        font=(self.family, size, 'bold' if bold else 'normal'), **kwargs)

    @property
    def computer_turn(self):
        return self.active_mode != MODES[0] and self.match.turn == 'O'

    def play_click(self):
        self.sounds.play('click')

    def _shortcut(self, action):
        self.play_click()
        action()
        return 'break'

    def toggle_sound(self):
        self.sounds.set_enabled(not self.sounds.enabled)
        self.sound_button.text = 'Ήχος: ενεργός' if self.sounds.enabled else 'Ήχος: σίγαση'
        self.sound_button.draw()
        if self.sounds.enabled:
            self.play_click()

    def _build_ui(self):
        sidebar = tk.Frame(self, bg=PANEL, width=276, padx=22, pady=26)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        brand = tk.Frame(sidebar, bg=PANEL)
        brand.pack(fill='x', pady=(0, 25))
        logo = tk.Canvas(brand, bg=PANEL, width=42, height=42, highlightthickness=0)
        logo.pack(side='left', padx=(0, 10))
        rounded(logo, 0, 0, 42, 42, 12, fill='#2d3451', outline='')
        logo.create_line(10, 10, 21, 21, fill=TEAL, width=3, capstyle='round')
        logo.create_line(21, 10, 10, 21, fill=TEAL, width=3, capstyle='round')
        logo.create_oval(23, 24, 34, 35, outline=CORAL, width=3)
        self.label(brand, 'Τρίλιζα', size=23, bold=True, background=PANEL).pack(side='left')
        self.label(sidebar, 'ΤΟ ΔΙΚΟ ΣΟΥ ΜΙΚΡΟ ΔΙΑΛΕΙΜΜΑ', size=8, color=MUTED,
                   background=PANEL).pack(anchor='w', pady=(0, 22))
        self.label(sidebar, 'Αντίπαλος', size=10, color=MUTED,
                   background=PANEL).pack(anchor='w', pady=(0, 9))
        self.local_button = ActionButton(sidebar, 'Με έναν φίλο', lambda: self.select_mode(MODES[0]),
                                         font=(self.family, 11), background=PANEL)
        self.local_button.pack(fill='x', pady=(0, 7))
        self.computer_button = ActionButton(sidebar, 'Με υπολογιστή', self.select_computer,
                                            font=(self.family, 11), background=PANEL)
        self.computer_button.pack(fill='x')
        self.label(sidebar, 'Βρες τον ρυθμό σου', size=10, color=MUTED,
                   background=PANEL).pack(anchor='w', pady=(24, 9))
        levels = tk.Frame(sidebar, bg=PANEL)
        levels.pack(fill='x')
        for column in range(2):
            levels.columnconfigure(column, weight=1, uniform='level')
        for index, title in enumerate(('Εύκολο', 'Μέτριο', 'Δύσκολο', 'Αήττητο')):
            mode = MODES[index+1]
            button = ActionButton(levels, title, lambda mode=mode: self.select_mode(mode),
                                  font=(self.family, 10), height=43, background=PANEL)
            button.grid(row=index//2, column=index%2, sticky='ew',
                        padx=(0, 4) if index%2 == 0 else (4, 0), pady=4)
            self.mode_buttons[mode] = button
        self.label(sidebar, textvariable=self.detail, size=10, color=MUTED,
                   background=PANEL, justify='left', wraplength=225,
                   anchor='nw').pack(fill='x', pady=(14, 0))
        tk.Frame(sidebar, bg=PANEL).pack(fill='both', expand=True)
        ActionButton(sidebar, 'Πώς παίζεται;   ↗', self.show_help,
                     font=(self.family, 10), height=40, background=PANEL).pack(fill='x', pady=(12, 7))
        ActionButton(sidebar, 'Μηδενισμός σκορ', self.reset_session,
                     font=(self.family, 10), height=40, background=PANEL).pack(fill='x')
        self.label(sidebar, 'OFFLINE  ·  ΧΩΡΙΣ ΔΙΑΦΗΜΙΣΕΙΣ', size=8, color=MUTED,
                   background=PANEL).pack(pady=(18, 0))

        main = tk.Frame(self, bg=BG, padx=30, pady=25)
        main.pack(side='left', fill='both', expand=True)
        top = tk.Frame(main, bg=BG)
        top.pack(fill='x')
        self.label(top, textvariable=self.round_text, size=10, color=PURPLE, bold=True).pack(side='left')
        self.sound_button = ActionButton(top, 'Ήχος: ενεργός', self.toggle_sound,
                                          font=(self.family, 9), height=30,
                                          on_activate=lambda: None)
        self.sound_button.configure(width=145)
        self.sound_button.pack(side='right')
        self.label(main, textvariable=self.status, size=23, bold=True).pack(anchor='w', pady=(18, 2))
        self.label(main, textvariable=self.subtitle, size=10, color=MUTED).pack(anchor='w', pady=(0, 16))
        scores = tk.Frame(main, bg=BG)
        scores.pack(fill='x')
        for column, (key, title, color) in enumerate((('X', 'Παίκτης X', TEAL),
                                                    ('draw', 'Ισοπαλίες', PURPLE),
                                                    ('O', 'Παίκτης O', CORAL))):
            scores.columnconfigure(column, weight=1, uniform='score')
            card = ScoreCard(scores, title, color, family=self.family)
            card.grid(row=0, column=column, sticky='ew', padx=(0, 10) if column < 2 else 0)
            self.score_cards[key] = card
        board_host = tk.Frame(main, bg=BG)
        board_host.pack(fill='both', expand=True, pady=(15, 12))
        board = tk.Frame(board_host, bg=BG)
        def resize_board(event):
            side = max(1, min(event.width, event.height, 470))
            board.place(relx=.5, rely=.5, anchor='center', width=side, height=side)
        board_host.bind('<Configure>', resize_board)
        for i in range(3):
            board.rowconfigure(i, weight=1, uniform='cell')
            board.columnconfigure(i, weight=1, uniform='cell')
        for i in range(9):
            cell = BoardCell(board, i, lambda cell=i: self.handle_click(cell), family=self.family)
            cell.grid(row=i//3, column=i%3, sticky='nsew', padx=3, pady=3)
            self.buttons[i] = cell
        self.next_button = ActionButton(main, 'Επόμενος γύρος   →', self.next_round,
                                        kind='primary', font=(self.family, 11, 'bold'), height=47)
        self.next_button.pack(fill='x')
        self.label(main, '1–9: κίνηση   ·   Ctrl+N: γύρος   ·   F1: βοήθεια   ·   F2: ήχος',
                   size=9, color=MUTED).pack(pady=(13, 0))

    def _render(self):
        outcome = self.match.outcome
        line = winning_line(self.match.board)
        computer = self.active_mode != MODES[0]
        for i, button in self.buttons.items():
            symbol = self.match.board[i]
            button.set_cell(symbol, not (symbol or outcome or self.computer_turn),
                            i in line, self.match.turn)
        titles = {'X': 'Εσύ · X' if computer else 'Παίκτης X',
                  'O': 'Υπολογιστής · O' if computer else 'Παίκτης O', 'draw': 'Ισοπαλίες'}
        for key, card in self.score_cards.items():
            card.set_value(self.scores[key], titles[key])
        self.local_button.set_selected(not computer)
        self.computer_button.set_selected(computer)
        for mode, button in self.mode_buttons.items():
            button.set_selected(mode == self.active_mode)
        self.detail.set(DETAILS[MODES.index(self.active_mode)])
        self.round_text.set(f'ΓΥΡΟΣ {self.round_number:02d}')
        if outcome == 'draw':
            self.status.set('Στα ίσα. Άλλη μία;')
            self.subtitle.set('Καλή αναμέτρηση. Ο επόμενος γύρος είναι δικός σας.')
        elif outcome:
            self.status.set('Τα κατάφερες!' if computer and outcome == 'X' else
                            'Νίκη του υπολογιστή.' if computer else f'Νίκη για τον {outcome}!')
            self.subtitle.set('Τρία στη σειρά. Ώρα για τη ρεβάνς!')
        else:
            self.status.set('Ο υπολογιστής σκέφτεται…' if self.computer_turn else
                            'Η σειρά σου.' if computer else f'Η σειρά του {self.match.turn}.')
            self.subtitle.set('Παρατήρησε, σχεδίασε, παίξε.' if self.computer_turn else
                              'Διάλεξε ένα κελί και φτιάξε τη δική σου τριάδα.')

    def handle_click(self, cell):
        if not self.computer_turn:
            self._play(cell)

    def _play(self, cell):
        player = self.match.turn
        if not self.match.play(cell):
            return
        outcome = self.match.outcome
        if outcome:
            self.scores[outcome] += 1
        if outcome == 'draw':
            sound = 'draw'
        elif outcome:
            sound = 'lose' if outcome == 'O' and self.active_mode != MODES[0] else 'win'
        else:
            sound = 'move_x' if player == 'X' else 'move_o'
        self.sounds.play(sound)
        self._render()
        self._schedule_computer()

    def _schedule_computer(self):
        if self.computer_turn and not self.match.outcome and self.pending is None:
            self.pending = self.after(420, self._computer_move)

    def _computer_move(self):
        self.pending = None
        if not self.computer_turn or self.match.outcome:
            return
        self._play(choose_move(self.match.board, 'O', DIFFICULTIES[self.active_mode]))

    def _cancel_pending(self):
        if self.pending is not None:
            self.after_cancel(self.pending)
            self.pending = None

    def _new_round(self):
        self._cancel_pending()
        self.match = Match(turn=self.starter)
        self._render()
        self._schedule_computer()

    def next_round(self):
        if any(self.match.board) and not self.match.outcome:
            if not messagebox.askyesno('Νέος γύρος', 'Να εγκαταλειφθεί ο τρέχων γύρος;', parent=self):
                return
        self.round_number += 1
        self.starter = 'O' if self.starter == 'X' else 'X'
        self._new_round()

    def reset_session(self):
        if messagebox.askyesno('Μηδενισμός', 'Να διαγραφούν τα σκορ και να αρχίσει νέο παιχνίδι;', parent=self):
            self._reset_session()

    def _reset_session(self):
        self.scores = {'X': 0, 'O': 0, 'draw': 0}
        self.round_number, self.starter = 1, 'X'
        self._new_round()

    def select_computer(self):
        self.select_mode(self.last_computer_mode)

    def select_mode(self, mode):
        self.mode.set(mode)
        self.change_mode()

    def change_mode(self, event=None):
        if self.mode.get() == self.active_mode:
            return
        if any(self.match.board) or any(self.scores.values()):
            if not messagebox.askyesno('Αλλαγή παιχνιδιού', 'Η αλλαγή μηδενίζει τον γύρο και τα σκορ. Συνέχεια;', parent=self):
                self.mode.set(self.active_mode)
                return
        self.active_mode = self.mode.get()
        if self.active_mode != MODES[0]:
            self.last_computer_mode = self.active_mode
        self._reset_session()

    def _key_move(self, event):
        if event.char and event.char in '123456789':
            self.handle_click(int(event.char)-1)

    def show_help(self):
        popup = tk.Toplevel(self)
        popup.title('Πώς παίζεται')
        popup.configure(bg=PANEL)
        popup.resizable(False, False)
        popup.transient(self)
        content = tk.Frame(popup, bg=PANEL, padx=28, pady=26)
        content.pack()
        self.label(content, 'Μια απλή ιδέα. Πολλές αναμετρήσεις.', size=16, bold=True,
                   background=PANEL).pack(anchor='w', pady=(0, 18))
        instructions = (
            'Φτιάξε τρία ίδια σύμβολα σε γραμμή, στήλη ή διαγώνιο.\n\n'
            'Με φίλο: μοιράζεστε το ίδιο ταμπλό. Με υπολογιστή: είσαι X.\n'
            'Ο πρώτος παίκτης αλλάζει σε κάθε νέο γύρο.\n\n'
            'Εύκολο  /  Τυχαίες κινήσεις, για ζέσταμα.\n'
            'Μέτριο  /  Βλέπει απειλές, αλλά αφήνει ανοίγματα.\n'
            'Δύσκολο  /  Σκέφτεται στρατηγικά, αλλά μπορείς να το κερδίσεις.\n'
            'Αήττητο  /  Το καλύτερο δυνατό αποτέλεσμα είναι ισοπαλία.\n\n'
            '1–9: κίνηση, από πάνω αριστερά προς κάτω δεξιά.\n'
            'Tab και Space/Enter: επιλογή και ενεργοποίηση κουμπιών.\n'
            'Ctrl+N: νέος γύρος. F1: βοήθεια.\n\n'
            'Ήχοι: κουμπί πάνω δεξιά ή F2 για σίγαση/ενεργοποίηση.\n\n'
            'Τα σκορ ισχύουν μόνο όσο είναι ανοιχτή η εφαρμογή.\n'
            f'Έκδοση {VERSION} · Χωρίς σύνδεση στο διαδίκτυο.'
        )
        self.label(content, instructions, size=10, color=MUTED, background=PANEL,
                   justify='left', wraplength=475).pack(anchor='w')
        ActionButton(content, 'Πάμε να παίξουμε   →', popup.destroy, kind='primary',
                     font=(self.family, 11, 'bold'), background=PANEL,
                     on_activate=self.play_click).pack(fill='x', pady=(22, 0))
        popup.bind('<Escape>', lambda event: popup.destroy())
        popup.update_idletasks()
        popup.geometry(f'+{self.winfo_rootx()+80}+{self.winfo_rooty()+40}')

    def close(self):
        self._cancel_pending()
        self.sounds.close()
        self.destroy()
