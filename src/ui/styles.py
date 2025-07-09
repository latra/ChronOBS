import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable

from models.types import StyleColors


class StyleManager:
    
    def __init__(self) -> None:
        self._colors: Dict[str, str] = {
            'bg_primary': StyleColors.BG_PRIMARY,
            'bg_secondary': StyleColors.BG_SECONDARY,
            'bg_accent': StyleColors.BG_ACCENT,
            'purple_primary': StyleColors.PURPLE_PRIMARY,
            'purple_secondary': StyleColors.PURPLE_SECONDARY,
            'purple_light': StyleColors.PURPLE_LIGHT,
            'text_primary': StyleColors.TEXT_PRIMARY,
            'text_secondary': StyleColors.TEXT_SECONDARY,
        }
    
    def create_button(self, parent: tk.Widget, text: str, command: Callable, 
                     style: str = "primary", state: str = "normal") -> tk.Button:

        if style == "primary":
            return self._create_primary_button(parent, text, command, state)
        elif style == "secondary":
            return self._create_secondary_button(parent, text, command, state)
        elif style == "big":
            return self._create_big_button(parent, text, command, state)
        else:
            return self._create_primary_button(parent, text, command, state)
    
    def _create_primary_button(self, parent: tk.Widget, text: str, 
                              command: Callable, state: str) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self._colors['purple_primary'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            borderwidth=0,
            padx=20,
            pady=10,
            cursor='hand2',
            state=state
        )
        
        def on_enter(e):
            if btn['state'] == 'normal':
                btn.config(bg=self._colors['purple_secondary'])
        
        def on_leave(e):
            if btn['state'] == 'normal':
                btn.config(bg=self._colors['purple_primary'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def _create_secondary_button(self, parent: tk.Widget, text: str, 
                                command: Callable, state: str) -> tk.Button:

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self._colors['bg_accent'],
            fg=self._colors['text_primary'],
            font=('Segoe UI', 10),
            relief='solid',
            borderwidth=1,
            padx=15,
            pady=8,
            cursor='hand2',
            state=state,
            highlightbackground=self._colors['purple_primary'],
            highlightcolor=self._colors['purple_primary'],
            highlightthickness=1
        )
        
        def on_enter(e):
            if btn['state'] == 'normal':
                btn.config(bg=self._colors['purple_primary'], fg='white')
        
        def on_leave(e):
            if btn['state'] == 'normal':
                btn.config(bg=self._colors['bg_accent'], fg=self._colors['text_primary'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def _create_big_button(self, parent: tk.Widget, text: str, 
                          command: Callable, state: str) -> tk.Button:

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self._colors['purple_primary'],
            fg='white',
            font=('Segoe UI', 14, 'bold'),
            relief='flat',
            borderwidth=0,
            padx=30,
            pady=15,
            cursor='hand2',
            state=state
        )
        
        def on_enter(e):
            if btn['state'] == 'normal':
                btn.config(bg=self._colors['purple_secondary'])
        
        def on_leave(e):
            if btn['state'] == 'normal':
                btn.config(bg=self._colors['purple_primary'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def create_label(self, parent: tk.Widget, text: str, style: str = "normal") -> tk.Label:

        if style == "title":
            return tk.Label(
                parent,
                text=text,
                bg=self._colors['bg_primary'],
                fg=self._colors['purple_light'],
                font=('Segoe UI', 24, 'bold')
            )
        elif style == "subtitle":
            return tk.Label(
                parent,
                text=text,
                bg=self._colors['bg_primary'],
                fg=self._colors['text_primary'],
                font=('Segoe UI', 12)
            )
        elif style == "status":
            return tk.Label(
                parent,
                text=text,
                bg=self._colors['bg_primary'],
                fg=self._colors['text_secondary'],
                font=('Segoe UI', 9, 'italic')
            )
        else:  # normal
            return tk.Label(
                parent,
                text=text,
                bg=self._colors['bg_primary'],
                fg=self._colors['text_primary'],
                font=('Segoe UI', 10)
            )
    
    def create_entry(self, parent: tk.Widget, width: int = 30) -> tk.Entry:

        entry = tk.Entry(
            parent,
            bg=self._colors['bg_secondary'],
            fg=self._colors['text_primary'],
            font=('Segoe UI', 10),
            relief='solid',
            borderwidth=2,
            width=width,
            insertbackground=self._colors['purple_light']
        )
        
        def on_focus_in(e):
            entry.config(highlightbackground=self._colors['purple_light'],
                        highlightcolor=self._colors['purple_light'],
                        highlightthickness=2)
        
        def on_focus_out(e):
            entry.config(highlightthickness=0)
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        return entry
    
    def create_frame(self, parent: tk.Widget) -> tk.Frame:

        return tk.Frame(
            parent,
            bg=self._colors['bg_primary']
        )
    
    def get_text_widget_config(self) -> Dict[str, Any]:

        return {
            'bg': self._colors['bg_secondary'],
            'fg': self._colors['text_primary'],
            'font': ('Consolas', 9),
            'borderwidth': 2,
            'relief': 'solid',
            'selectbackground': self._colors['purple_primary'],
            'selectforeground': self._colors['text_primary'],
            'insertbackground': self._colors['purple_light']
        }
    
    @property
    def colors(self) -> Dict[str, str]:
        """Acceder a los colores del tema"""
        return self._colors.copy() 