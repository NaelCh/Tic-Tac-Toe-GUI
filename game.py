"""Greek desktop Tic Tac Toe. No third-party runtime dependencies."""
import random
import tkinter as tk
from tkinter import messagebox, ttk
from engine import Match, best_move, winning_line

BG, INK, MUTED, GREEN, WHITE = '#f4f2ec', '#203731', '#64756c', '#18755b', '#ffffff'
MODES = ('Δύο παίκτες', 'Υπολογιστής · εύκολο', 'Υπολογιστής · αήττητο')


class TicTacToe(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Τρίλιζα | Μια κίνηση ακόμα')
        self.geometry('560x960')
        self.minsize(520, 850)
        self.configure(bg=BG)
        self.match = Match()
        self.scores = {'X': 0, 'O': 0, 'draw': 0}
        self.round_number, self.starter, self.pending = 1, 'X', None
        self.mode = tk.StringVar(value=MODES[0])
        self.active_mode = MODES[0]
        self.status, self.subtitle = tk.StringVar(), tk.StringVar()
        self.score_text, self.buttons = {}, {}
        self._build_ui()
        self._render()
        self.bind('<Control-n>', lambda event: self.next_round())
        self.bind('<F1>', lambda event: self.show_help())
        self.bind('<KeyPress>', self._key_move)
        self.protocol('WM_DELETE_WINDOW', self.close)

    @property
    def computer_turn(self):
        return self.active_mode != MODES[0] and self.match.turn == 'O'

    def _label(self, parent, text):
        return tk.Label(parent, text=text, bg=BG, fg=INK, font=('DejaVu Sans', 10))

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TCombobox', padding=8)
        outer = tk.Frame(self, bg=BG, padx=28, pady=22)
        outer.pack(fill='both', expand=True)
        self._label(outer, 'ΠΑΙΞΕ • ΣΚΕΨΟΥ • ΞΑΝΑΠΑΙΞΕ').pack(anchor='w')
        tk.Label(outer, text='Τρίλιζα', bg=BG, fg=INK,
                 font=('DejaVu Sans', 32, 'bold')).pack(anchor='w', pady=(5,0))
        self._label(outer, 'Ένα μικρό παιχνίδι. Μια καλή αναμέτρηση.').pack(anchor='w', pady=(0,18))
        row = tk.Frame(outer, bg=BG)
        row.pack(fill='x')
        self._label(row, 'Τρόπος παιχνιδιού').pack(side='left')
        tk.Button(row, text='Πώς παίζεται;', command=self.show_help, bg=BG,
                  fg=GREEN, relief='flat', cursor='hand2').pack(side='right')
        selector = ttk.Combobox(outer, textvariable=self.mode, values=MODES, state='readonly', font=('DejaVu Sans',11))
        selector.pack(fill='x', pady=(7,16))
        selector.bind('<<ComboboxSelected>>', self.change_mode)
        scores = tk.Frame(outer, bg=BG)
        scores.pack(fill='x')
        for column, (key,title) in enumerate((('X','ΠΑΙΚΤΗΣ X'), ('draw','ΙΣΟΠΑΛΙΕΣ'), ('O','ΠΑΙΚΤΗΣ O'))):
            scores.columnconfigure(column, weight=1, uniform='score')
            card = tk.Frame(scores, bg=WHITE, padx=6, pady=10)
            card.grid(row=0, column=column, sticky='ew', padx=3)
            tk.Label(card, text=title, bg=WHITE, fg=MUTED, font=('DejaVu Sans',9)).pack()
            self.score_text[key] = tk.StringVar(value='0')
            tk.Label(card, textvariable=self.score_text[key], bg=WHITE, fg=INK,
                     font=('DejaVu Sans',22,'bold')).pack()
        tk.Label(outer, textvariable=self.status, bg=BG, fg=GREEN,
                 font=('DejaVu Sans',16,'bold')).pack(pady=(17,2))
        tk.Label(outer, textvariable=self.subtitle, bg=BG, fg=MUTED,
                 font=('DejaVu Sans',10)).pack(pady=(0,12))
        board_host = tk.Frame(outer, bg=BG)
        board_host.pack(fill='both', expand=True)
        board = tk.Frame(board_host, bg=BG)
        def resize_board(event):
            side = min(event.width, event.height)
            board.place(relx=.5, rely=.5, anchor='center', width=side, height=side)
        board_host.bind('<Configure>', resize_board)
        for i in range(3):
            board.rowconfigure(i, weight=1, uniform='cell')
            board.columnconfigure(i, weight=1, uniform='cell')
        for i in range(9):
            button = tk.Button(board, text='', bg=WHITE, activebackground='#e1eee5',
                               fg=GREEN, disabledforeground=GREEN, relief='flat', bd=0,
                               font=('DejaVu Sans',30,'bold'), cursor='hand2',
                               takefocus=True, command=lambda cell=i: self.handle_click(cell))
            button.grid(row=i//3, column=i%3, sticky='nsew', padx=4, pady=4)
            self.buttons[i] = button
        actions = tk.Frame(outer, bg=BG)
        actions.pack(fill='x', pady=(16,0))
        tk.Button(actions, text='Επόμενος γύρος →', command=self.next_round,
                  bg=GREEN, fg=WHITE, activebackground='#10563f', activeforeground=WHITE,
                  relief='flat', padx=16, pady=11, cursor='hand2',
                  font=('DejaVu Sans',11,'bold')).pack(side='left')
        tk.Button(actions, text='Μηδενισμός σκορ', command=self.reset_session,
                  bg=BG, fg=MUTED, relief='flat', cursor='hand2').pack(side='right')
        self._label(outer, '1–9: κίνηση   •   Ctrl+N: νέος γύρος   •   F1: βοήθεια').pack(pady=(14,0))

    def _render(self):
        outcome = self.match.outcome
        line = winning_line(self.match.board)
        for i, button in self.buttons.items():
            symbol = self.match.board[i]
            button.configure(text=symbol, bg='#d3e9d8' if i in line else WHITE,
                             disabledforeground=GREEN if symbol == 'X' else '#aa573e',
                             state='disabled' if symbol or outcome or self.computer_turn else 'normal')
        for key, value in self.score_text.items():
            value.set(str(self.scores[key]))
        if outcome == 'draw':
            self.status.set('Ισοπαλία. Άλλη μία;')
        elif outcome:
            self.status.set('Κέρδισε ο υπολογιστής!' if outcome == 'O' and self.active_mode != MODES[0]
                            else f'Νίκη για τον {outcome}!')
        else:
            self.status.set('Ο υπολογιστής σκέφτεται…' if self.computer_turn else f'Σειρά του {self.match.turn}')
        self.subtitle.set(f'Γύρος {self.round_number}  ·  ' +
                          ('Ο γύρος ολοκληρώθηκε' if outcome else 'Τρία στη σειρά για τη νίκη'))

    def handle_click(self, cell):
        if not self.computer_turn:
            self._play(cell)

    def _play(self, cell):
        if not self.match.play(cell):
            return
        if self.match.outcome:
            self.scores[self.match.outcome] += 1
        self._render()
        self._schedule_computer()

    def _schedule_computer(self):
        if self.computer_turn and not self.match.outcome and self.pending is None:
            self.pending = self.after(350, self._computer_move)

    def _computer_move(self):
        self.pending = None
        if not self.computer_turn or self.match.outcome:
            return
        cell = (random.choice([i for i, value in enumerate(self.match.board) if not value])
                if self.active_mode == MODES[1] else best_move(self.match.board, 'O'))
        self._play(cell)

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

    def change_mode(self, event=None):
        if self.mode.get() == self.active_mode:
            return
        if any(self.match.board) or any(self.scores.values()):
            if not messagebox.askyesno('Αλλαγή παιχνιδιού', 'Η αλλαγή μηδενίζει τον γύρο και τα σκορ. Συνέχεια;', parent=self):
                self.mode.set(self.active_mode)
                return
        self.active_mode = self.mode.get()
        self._reset_session()

    def _key_move(self, event):
        if event.char and event.char in '123456789' and not isinstance(self.focus_get(), ttk.Combobox):
            self.handle_click(int(event.char)-1)

    def show_help(self):
        messagebox.showinfo('Πώς παίζεται', 'Συμπλήρωσε τρία ίδια σύμβολα σε γραμμή, στήλη ή διαγώνιο.\n\n'
                            'Παίξτε δύο άτομα ή επίλεξε υπολογιστή. Εσύ παίζεις με X, ο υπολογιστής με O. '
                            'Στο αήττητο επίπεδο, το καλύτερο δυνατό αποτέλεσμα είναι ισοπαλία.\n\n'
                            'Οι παίκτες ξεκινούν εναλλάξ κάθε γύρο. Τα πλήκτρα 1–9 αντιστοιχούν στα κελιά '
                            'από πάνω αριστερά προς τα κάτω δεξιά.\n\n'
                            'Τα σκορ κρατούνται μόνο όσο είναι ανοιχτή η εφαρμογή.\n'
                            'Έκδοση 1.0.0 · Λειτουργεί χωρίς σύνδεση στο διαδίκτυο.', parent=self)

    def close(self):
        self._cancel_pending()
        self.destroy()
