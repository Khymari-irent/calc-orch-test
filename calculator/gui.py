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
    history_frame = tk.Frame(root, bg="#202124")
    history = tk.Listbox(history_frame, height=4, bg="#202124", fg="#bdc1c6", highlightthickness=0, relief="flat", activestyle="none")
    scrollbar = tk.Scrollbar(history_frame, orient="vertical", command=history.yview)
    history.configure(yscrollcommand=scrollbar.set)
    history_entries: list[str] = []
    history.pack(side="left", fill="both", expand=True)

    def append(value: str) -> None:
        expression.set(expression.get() + value)

    def clear() -> None:
        expression.set("")

    def backspace() -> None:
        expression.set(expression.get()[:-1])

    def calculate() -> None:
        original = expression.get()
        try:
            result = evaluate(original)
            expression.set(str(result))
            history_entries.append(f"{original} = {result}")
            history.delete(0, tk.END)
            for entry in history_entries:
                history.insert(tk.END, entry)
            if history_frame.winfo_manager() == "":
                history_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=4, pady=(0, 10))
            if len(history_entries) > 4 and scrollbar.winfo_manager() == "":
                scrollbar.pack(side="right", fill="y", padx=(6, 0))
            elif len(history_entries) <= 4 and scrollbar.winfo_manager():
                scrollbar.pack_forget()
        except CalculatorError as error:
            messagebox.showerror("Calculator error", str(error), parent=root)

    buttons = [(".", 2, 0), ("Clear", 2, 1), ("<", 2, 2), ("/", 2, 3),
               ("7", 3, 0), ("8", 3, 1), ("9", 3, 2), ("*", 3, 3),
               ("4", 4, 0), ("5", 4, 1), ("6", 4, 2), ("-", 4, 3),
               ("1", 5, 0), ("2", 5, 1), ("3", 5, 2), ("+", 5, 3),
               ("0", 6, 0), ("(", 6, 1), (")", 6, 2), ("=", 6, 3)]
    for label, row, column in buttons:
        command = {"Clear": clear, "<": backspace, "=": calculate}.get(label, lambda value=label: append(value))
        background = "#8ab4f8" if label == "=" else "#5f6368" if label == "Clear" else "#3c4043"
        foreground = "#202124" if label == "=" else "#ffffff"
        tk.Button(root, text=label, font=("Segoe UI", 14), bg=background, fg=foreground, activebackground="#aecbfa", activeforeground="#202124", relief="flat", width=5, command=command).grid(row=row, column=column, sticky="nsew", padx=4, pady=4, ipady=7)
    for column in range(4):
        root.grid_columnconfigure(column, weight=1)
    for row in range(2, 7):
        root.grid_rowconfigure(row, weight=1)
    display.focus_set()
    root.bind("<Return>", lambda _event: calculate())
    root.bind("<Escape>", lambda _event: clear())
    root.mainloop()
