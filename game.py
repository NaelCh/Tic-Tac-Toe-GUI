import tkinter as tk

BOARD_SIZE = 3
SYMBOLS = ("x", "0")


class TicTacToe(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tic Tac Toe")
        self.current_player = SYMBOLS[0]
        self.board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

########################################################################3
# #import tkinter as tk
#
# BOARD_SIZE = 3
# SYMBOLS = ("X", "O")
#
#
# class TicTacToe(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Tic Tac Toe")
#         self.current_player = SYMBOLS[0]
#         self.board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
#         self.buttons = {}
#
#         self._build_ui()
#
#     def _build_ui(self):
#         # Grid 3x3 για το ταμπλό
#         for i in range(BOARD_SIZE):
#             self.grid_columnconfigure(i, weight=1, minsize=100)
#             self.grid_rowconfigure(i, weight=1, minsize=100)
#
#         for r in range(BOARD_SIZE):
#             for c in range(BOARD_SIZE):
#                 btn = tk.Button(
#                     self,
#                     text="",
#                     font=("Helvetica", 28, "bold"),
#                     width=3,
#                     height=1,
#                     command=lambda r=r, c=c: self.handle_click(r, c)
#                 )
#                 btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
#                 self.buttons[(r, c)] = btn
#
#         # Γραμμή κατάστασης + κουμπί reset
#         status_row = BOARD_SIZE
#         self.grid_rowconfigure(status_row, weight=0)
#         self.status = tk.StringVar(value=f"Σειρά: {self.current_player}")
#         status_lbl = tk.Label(self, textvariable=self.status, font=("Helvetica", 12))
#         status_lbl.grid(row=status_row, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))
#
#         reset_btn = tk.Button(self, text="Reset", command=self.reset_board)
#         reset_btn.grid(row=status_row, column=2, sticky="e", padx=8, pady=(0, 8))
#
#     def handle_click(self, r, c):
#         # Αγνοεί κλικ αν το κελί έχει ήδη παιχτεί
#         if self.board[r][c]:
#             return
#
#         # Θέσε σύμβολο στο state + στο κουμπί
#         self.board[r][c] = self.current_player
#         self.buttons[(r, c)].config(text=self.current_player, state="disabled")
#
#         # (Το check_winner θα μπει στο βήμα 2)
#         self._swap_player()
#
#     def _swap_player(self):
#         self.current_player = SYMBOLS[1] if self.current_player == SYMBOLS[0] else SYMBOLS[0]
#         self.status.set(f"Σειρά: {self.current_player}")
#
#     def reset_board(self):
#         self.current_player = SYMBOLS[0]
#         self.status.set(f"Σειρά: {self.current_player}")
#         for (r, c), btn in self.buttons.items():
#             btn.config(text="", state="normal")
#         self.board = [["" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
#
#
# if __name__ == "__main__":
#     app = TicTacToe()
#     app.mainloop()
