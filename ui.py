"""Small, dependency-free canvas controls for the desktop interface."""
import tkinter as tk

BG = '#101321'
PANEL = '#181c30'
TILE = '#222840'
TEXT = '#f2f4ff'
MUTED = '#a0aac9'
TEAL = '#72efcf'
CORAL = '#ffa28f'
PURPLE = '#baadff'


def rounded(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    radius = min(radius, (x2-x1)/2, (y2-y1)/2)
    return canvas.create_polygon(
        x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
        x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
        x1, y2, x1, y2-radius, x1, y1+radius, x1, y1,
        smooth=True, splinesteps=24, **kwargs)


class ActionButton(tk.Canvas):
    def __init__(self, parent, text, command, *, font, kind='quiet',
                 height=44, background=BG, **kwargs):
        super().__init__(parent, height=height, width=1, bg=background,
                         highlightthickness=0, takefocus=True, cursor='hand2', **kwargs)
        self.text, self.command, self.font, self.kind = text, command, font, kind
        self.selected, self.hovered = False, False
        self.bind('<Configure>', lambda event: self.draw())
        self.bind('<Enter>', lambda event: self._hover(True))
        self.bind('<Leave>', lambda event: self._hover(False))
        self.bind('<FocusIn>', lambda event: self.draw())
        self.bind('<FocusOut>', lambda event: self.draw())
        self.bind('<Button-1>', self._click)
        self.bind('<Return>', lambda event: self.invoke())
        self.bind('<space>', lambda event: self.invoke())

    def _hover(self, value):
        self.hovered = value
        self.draw()

    def _click(self, event):
        self.focus_set()
        self.invoke()

    def invoke(self):
        self.command()

    def set_selected(self, value):
        if self.selected != value:
            self.selected = value
            self.draw()

    def draw(self):
        self.delete('all')
        width, height = self.winfo_width(), self.winfo_height()
        primary = self.kind == 'primary'
        fill = TEAL if primary else '#32334e' if self.selected else '#24293f'
        if self.hovered:
            fill = '#9af8df' if primary else '#383e59'
        outline = PURPLE if self.selected else '#343b57'
        if self.focus_get() == self:
            outline = TEAL
        rounded(self, 1, 1, width-1, height-1, 13, fill=fill,
                outline=outline if not primary else fill, width=2)
        self.create_text(width/2, height/2, text=self.text,
                         fill=BG if primary else TEXT, font=self.font)


class BoardCell(tk.Canvas):
    def __init__(self, parent, index, command, *, family):
        super().__init__(parent, width=100, height=100, bg=BG,
                         highlightthickness=0, takefocus=True, cursor='hand2')
        self.index, self.command, self.family = index, command, family
        self.symbol, self.preview, self.winning = '', 'X', False
        self.hovered, self.progress, self.animation = False, 1.0, None
        self.bind('<Configure>', lambda event: self.draw())
        self.bind('<Enter>', lambda event: self._hover(True))
        self.bind('<Leave>', lambda event: self._hover(False))
        self.bind('<FocusIn>', lambda event: self.draw())
        self.bind('<FocusOut>', lambda event: self.draw())
        self.bind('<Button-1>', self._click)
        self.bind('<Return>', lambda event: self.invoke())
        self.bind('<space>', lambda event: self.invoke())

    def _hover(self, value):
        self.hovered = value
        self.draw()

    def _click(self, event):
        if self['state'] == 'normal':
            self.focus_set()
            self.invoke()

    def invoke(self):
        if self['state'] == 'normal':
            self.command()

    def set_cell(self, symbol, playable, winning, preview):
        changed = self.symbol != symbol
        self.symbol, self.winning, self.preview = symbol, winning, preview
        self.configure(state='normal' if playable else 'disabled',
                       takefocus=playable, cursor='hand2' if playable else 'arrow')
        if changed:
            self._cancel_animation()
            self.progress = 0.0 if symbol else 1.0
        self.draw()
        if changed and symbol:
            self._animate()

    def _cancel_animation(self):
        if self.animation is not None:
            self.after_cancel(self.animation)
            self.animation = None

    def _animate(self):
        self.animation = None
        self.progress = min(1.0, self.progress+.18)
        self.draw()
        if self.progress < 1:
            self.animation = self.after(20, self._animate)

    def draw(self):
        self.delete('all')
        width, height = self.winfo_width(), self.winfo_height()
        size = min(width, height)
        playable = self['state'] == 'normal'
        hovered = self.hovered and playable
        fill = '#203e3c' if self.winning else '#2c3452' if hovered else TILE
        outline = TEAL if self.winning or (playable and self.focus_get() == self) else '#3c4968' if hovered else fill
        rounded(self, 3, 3, width-3, height-3, 22, fill=fill, outline=outline, width=2)
        symbol = self.symbol or (self.preview if hovered else '')
        if not symbol:
            self.create_text(width-18, height-17, text=str(self.index+1),
                             fill='#737f9f', font=(self.family, 9))
            return
        color = TEAL if symbol == 'X' else CORAL
        if not self.symbol:
            color = '#4d797a' if symbol == 'X' else '#805c60'
        progress = self.progress if self.symbol else 1
        cx, cy, radius = width/2, height/2, size*.22
        stroke = max(4, int(size*.065))
        if symbol == 'X':
            for fraction, start, end in (
                (min(1, progress*2), (cx-radius, cy-radius), (cx+radius, cy+radius)),
                (max(0, progress*2-1), (cx+radius, cy-radius), (cx-radius, cy+radius)),
            ):
                if fraction:
                    ex = start[0]+(end[0]-start[0])*fraction
                    ey = start[1]+(end[1]-start[1])*fraction
                    self.create_line(*start, ex, ey, fill=color, width=stroke, capstyle='round')
        elif progress >= 1:
            self.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                             outline=color, width=stroke)
        else:
            self.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=90,
                            extent=-359*progress, style='arc', outline=color, width=stroke)

    def destroy(self):
        self._cancel_animation()
        super().destroy()


class ScoreCard(tk.Canvas):
    def __init__(self, parent, title, color, *, family):
        super().__init__(parent, height=74, width=1, bg=BG, highlightthickness=0)
        self.title, self.color, self.family, self.value = title, color, family, 0
        self.bind('<Configure>', lambda event: self.draw())

    def set_value(self, value, title):
        self.value, self.title = value, title
        self.draw()

    def draw(self):
        self.delete('all')
        width = self.winfo_width()
        rounded(self, 1, 1, width-1, 73, 16, fill=PANEL, outline=PANEL)
        self.create_text(16, 22, text=self.title, anchor='w', fill=MUTED,
                         font=(self.family, 9))
        self.create_text(16, 51, text=str(self.value), anchor='w', fill=self.color,
                         font=(self.family, 22, 'bold'))
        self.create_oval(width-27, 47, width-19, 55, fill=self.color, outline='')
