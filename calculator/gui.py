"""Tkinter GUI for the calculator foundation slice."""

import tkinter as tk
from tkinter import messagebox

from .engine import CalculatorError, evaluate


def launch() -> None:
    """Create and run the calculator window until the user closes it."""

    root = tk.Tk()
    root.title("Calculator")
    root.resizable(False, False)
    expression = tk.StringVar()
    display = tk.Entry(root, textvariable=expression, justify="right", font=("Segoe UI", 18), width=16)
    display.grid(row=0, column=0, columnspan=4, padx=8, pady=8)

    def append(value: str) -> None:
        expression.set(expression.get() + value)

    def clear() -> None:
        expression.set("")

    def calculate() -> None:
        try:
            expression.set(str(evaluate(expression.get())))
        except CalculatorError as error:
            messagebox.showerror("Calculator error", str(error), parent=root)

    buttons = [("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
               ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
               ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
               ("0", 4, 0), (".", 4, 1), ("(", 4, 2), (")", 4, 3)]
    for label, row, column in buttons:
        tk.Button(root, text=label, width=5, command=lambda value=label: append(value)).grid(row=row, column=column, padx=3, pady=3)
    tk.Button(root, text="+", width=11, command=lambda: append("+")).grid(row=5, column=0, columnspan=2, padx=3, pady=3)
    tk.Button(root, text="Clear", width=5, command=clear).grid(row=5, column=2, padx=3, pady=3)
    tk.Button(root, text="=", width=5, command=calculate).grid(row=5, column=3, padx=3, pady=3)
    display.focus_set()
    root.bind("<Return>", lambda _event: calculate())
    root.mainloop()
