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
    angle_mode = tk.StringVar(value="radians")
    display = tk.Entry(root, textvariable=expression, justify="right", font=("Segoe UI", 22), bg="#303134", fg="#f8f9fa", insertbackground="#f8f9fa", relief="flat", width=16)
    display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=4, pady=(4, 8), ipady=8)
    tk.Checkbutton(root, text="Degrees", variable=angle_mode, onvalue="degrees", offvalue="radians", bg="#202124", fg="#f8f9fa", selectcolor="#303134", activebackground="#202124", activeforeground="#ffffff").grid(row=1, column=0, columnspan=4, sticky="w", padx=4, pady=(0, 8))
    scientific_frame = tk.Frame(root, bg="#202124")
    scientific_buttons = [("sin", "sin(", "asin", "asin("), ("cos", "cos(", "acos", "acos("), ("tan", "tan(", "atan", "atan("), ("√", "sqrt(", "1/√x", "invsqrt("), ("x²", "square(", "1/x", "reciprocal("), ("log", "log(", "exp", "exp("), ("ln", "ln(", "eˣ", "exp("), ("abs", "abs(", "abs", "abs(")]
    scientific_widgets = []
    for column in range(4):
        scientific_frame.grid_columnconfigure(column, weight=1, uniform="keypad")
    for row in range((len(scientific_buttons) + 3) // 4):
        scientific_frame.grid_rowconfigure(row, weight=1, uniform="keypad")
    for index, (label, value, inverse_label, inverse_value) in enumerate(scientific_buttons):
        button = tk.Button(scientific_frame, text=label, font=("Segoe UI", 14), width=5, bg="#5f6368", fg="#ffffff", activebackground="#80868b", relief="flat", command=lambda item=value: append(item))
        button.grid(row=index // 4, column=index % 4, sticky="nsew", padx=4, pady=4, ipady=7)
        scientific_widgets.append((button, (label, value), (inverse_label, inverse_value)))
    scientific_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=4, pady=4)
    history_frame = tk.Frame(root, bg="#202124")
    history = tk.Listbox(history_frame, height=4, bg="#202124", fg="#bdc1c6", highlightthickness=0, relief="flat", activestyle="none")
    scrollbar = tk.Scrollbar(history_frame, orient="vertical", command=history.yview)
    history.configure(yscrollcommand=scrollbar.set)
    history_entries: list[str] = []
    history_frame.configure(height=72)
    history_frame.grid_propagate(False)
    history_frame.grid(row=9, column=0, columnspan=4, sticky="nsew", padx=4, pady=(8, 0))

    def recall_history(_event: tk.Event) -> None:
        selection = history.curselection()
        if selection:
            expression.set(history_entries[selection[0]].split(" = ", 1)[1])

    history.bind("<<ListboxSelect>>", recall_history)

    def append(value: str) -> None:
        expression.set(expression.get() + value)

    def clear() -> None:
        expression.set("")

    def backspace() -> None:
        expression.set(expression.get()[:-1])

    def calculate() -> None:
        original = expression.get()
        try:
            result = evaluate(original, angle_mode.get())
            expression.set(str(result))
            history_entries.append(f"{original} = {result}")
            if history.winfo_manager() == "":
                history.pack(side="left", fill="both", expand=True)
            history.delete(0, tk.END)
            for entry in history_entries:
                history.insert(tk.END, entry)
            history.configure(bg="#202124")
            if len(history_entries) > 4 and scrollbar.winfo_manager() == "":
                scrollbar.pack(side="right", fill="y", padx=(6, 0))
            elif len(history_entries) <= 4 and scrollbar.winfo_manager():
                scrollbar.pack_forget()
        except CalculatorError as error:
            messagebox.showerror("Calculator error", str(error), parent=root)

    buttons = [(".", 4, 0), ("Clear", 4, 1), ("<", 4, 2), ("/", 4, 3),
               ("7", 5, 0), ("8", 5, 1), ("9", 5, 2), ("*", 5, 3),
               ("4", 6, 0), ("5", 6, 1), ("6", 6, 2), ("-", 6, 3),
               ("1", 7, 0), ("2", 7, 1), ("3", 7, 2), ("+", 7, 3),
               ("0", 8, 0), ("(", 8, 1), (")", 8, 2), ("=", 8, 3)]
    for label, row, column in buttons:
        command = {"Clear": clear, "<": backspace, "=": calculate}.get(label, lambda value=label: append(value))
        background = "#8ab4f8" if label == "=" else "#5f6368" if label == "Clear" else "#3c4043"
        foreground = "#202124" if label == "=" else "#ffffff"
        tk.Button(root, text=label, font=("Segoe UI", 14), bg=background, fg=foreground, activebackground="#aecbfa", activeforeground="#202124", relief="flat", width=5, command=command).grid(row=row, column=column, sticky="nsew", padx=4, pady=4, ipady=7)
    for column in range(4):
        root.grid_columnconfigure(column, weight=1, uniform="keypad")
    for row in range(4, 9):
        root.grid_rowconfigure(row, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(9, weight=0)
    display.focus_set()
    root.bind("<Return>", lambda _event: calculate())
    root.bind("<Escape>", lambda _event: clear())
    def show_inverse_functions(_event: tk.Event) -> None:
        for button, _direct, inverse in scientific_widgets:
            button.configure(text=inverse[0], command=lambda item=inverse[1]: append(item))

    def show_direct_functions(_event: tk.Event) -> None:
        for button, direct, _inverse in scientific_widgets:
            button.configure(text=direct[0], command=lambda item=direct[1]: append(item))

    root.bind("<KeyPress-Shift_L>", show_inverse_functions)
    root.bind("<KeyRelease-Shift_L>", show_direct_functions)
    root.mainloop()
