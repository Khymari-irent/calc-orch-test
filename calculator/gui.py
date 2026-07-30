"""Tkinter GUI for the calculator foundation slice."""

import tkinter as tk
from tkinter import messagebox

from .engine import CalculatorError, evaluate


def launch() -> None:
    """Create and run the calculator window until the user closes it."""

    root = tk.Tk()
    root.title("Calculator")
    root.configure(bg="#202124", padx=12, pady=12)
    root.resizable(True, True)
    root.minsize(320, 420)
    expression = tk.StringVar()
    display = tk.Entry(root, textvariable=expression, justify="right", font=("Segoe UI", 22), bg="#303134", fg="#f8f9fa", insertbackground="#f8f9fa", relief="flat", width=16)
    display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=4, pady=(4, 14), ipady=8)

    def append(value: str) -> None:
        expression.set(expression.get() + value)

    def clear() -> None:
        expression.set("")

    def backspace() -> None:
        expression.set(expression.get()[:-1])

    def calculate() -> None:
        try:
            expression.set(str(evaluate(expression.get())))
        except CalculatorError as error:
            messagebox.showerror("Calculator error", str(error), parent=root)

    buttons = [(".", 1, 0), ("Clear", 1, 1), ("<", 1, 2), ("/", 1, 3),
               ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("*", 2, 3),
               ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("-", 3, 3),
               ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("+", 4, 3),
               ("0", 5, 0), ("(", 5, 1), (")", 5, 2), ("=", 5, 3)]
    for label, row, column in buttons:
        command = {"Clear": clear, "<": backspace, "=": calculate}.get(label, lambda value=label: append(value))
        background = "#8ab4f8" if label == "=" else "#5f6368" if label == "Clear" else "#3c4043"
        foreground = "#202124" if label == "=" else "#ffffff"
        tk.Button(root, text=label, font=("Segoe UI", 14), bg=background, fg=foreground, activebackground="#aecbfa", activeforeground="#202124", relief="flat", width=5, command=command).grid(row=row, column=column, sticky="nsew", padx=4, pady=4, ipady=7)
    for column in range(4):
        root.grid_columnconfigure(column, weight=1)
    for row in range(1, 6):
        root.grid_rowconfigure(row, weight=1)
    display.focus_set()
    root.bind("<Return>", lambda _event: calculate())
    root.bind("<Escape>", lambda _event: clear())
    root.mainloop()
