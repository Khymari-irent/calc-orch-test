# Calculator App Product Requirements Document

## 1. Overview

Build a simple calculator application in two incremental releases:

- **MVP 1:** Command-line interface (CLI) calculator.
- **MVP 2:** Graphical user interface (GUI) calculator built on the same calculation engine.

The product should provide reliable basic arithmetic, clear input validation, useful error messages, and automated tests.

## 2. Goals

- Perform common arithmetic operations accurately.
- Provide a small, understandable codebase that can evolve from CLI to GUI.
- Separate calculation logic from presentation and input handling.
- Handle invalid input and mathematical errors safely.
- Make core behavior testable through automated unit tests.

## 3. Non-goals

- Scientific, financial, graphing, or programmable-calculator features.
- Persistence of calculation history.
- User accounts, networking, cloud services, or external APIs.

## 4. Target users

People who need quick basic arithmetic on a computer and developers evaluating a small, testable application workflow.

## 5. Functional requirements

### Shared calculation engine

The calculation engine must support:

- Addition (`+`)
- Subtraction (`-`)
- Multiplication (`*`)
- Division (`/`)
- Integer and decimal operands
- Negative numbers
- Division-by-zero detection
- Clear, deterministic results

The engine should expose a small interface that does not depend on CLI or GUI libraries.

### MVP 1: CLI calculator

The CLI must:

1. Start from a documented command.
2. Accept and evaluate expressions containing one or more operations and parentheses, using standard operator precedence.
3. Display the calculated result.
4. Display a clear error for malformed expressions, unsupported syntax, invalid numbers, and division by zero.
5. Return a non-zero process exit code when the request cannot be completed.
6. Support a help or usage message.
7. Exit cleanly without requiring network access or persistent storage.

One-shot CLI usage is:

```text
python -m calculator "2 + 3 * 4"
python -m calculator "(10 - 2) / 4"
```

Running `python -m calculator` with no expression starts interactive mode. Interactive mode repeatedly accepts expressions, supports `Ans` as the previous successful result, prints clear errors without terminating the session, and exits when the user enters `quit`.

### MVP 2: GUI calculator

The GUI must:

- Display numeric buttons, decimal input, the four basic operators, equals, and clear.
- Display the current input and result.
- Support mouse or keyboard entry where practical.
- Prevent or clearly report invalid operations.
- Reuse the shared calculation engine from MVP 1.
- Remain responsive during normal use.
- Provide a clear way to close the application.

## 6. User stories

- As a user, I want to add two numbers so that I can get their sum quickly.
- As a user, I want to subtract, multiply, and divide numbers.
- As a user, I want invalid input to produce an understandable message.
- As a user, I want division by zero to be handled without crashing the application.
- As a CLI user, I want a help command so I can learn the syntax.
- As a GUI user, I want buttons and a display so I can calculate without memorizing commands.
- As a maintainer, I want the calculation logic separated from the interfaces so both UIs can be tested and extended.

## 7. Acceptance criteria

### MVP 1 acceptance

- Valid examples for all four operations return correct results.
- Decimal and negative operands work correctly.
- Invalid numbers and operators return clear errors and non-zero exit codes.
- Division by zero returns a clear error and does not crash.
- Help/usage documentation is available.
- Automated tests cover the calculation engine and CLI behavior.

### MVP 2 acceptance

- The GUI launches from documented instructions.
- A user can complete each basic arithmetic operation using the interface.
- Clear resets the current calculation.
- Invalid operations are safely handled.
- The GUI uses the shared calculation engine rather than duplicating arithmetic logic.
- Automated tests cover calculation logic and practical UI behavior where the chosen toolkit allows it.

## 8. Quality and technical requirements

- Use a supported runtime and document the required version.
- Keep dependencies minimal and documented.
- Follow the target repository's formatting and linting conventions.
- Include unit tests for each operation and error case.
- Add an end-to-end smoke test for the CLI.
- Document installation, usage, testing, and known limitations in `README.md`.
- Avoid storing secrets, user data, or unnecessary telemetry.

## 9. Release plan

### MVP 1 delivery slices

1. Define and implement the shared expression tokenizer/parser/evaluator.
2. Implement one-shot multi-operation CLI evaluation with parentheses and precedence.
3. Add automated tests for expressions, precedence, parentheses, errors, and division by zero.
4. Implement interactive mode with `Ans`, `quit`, and persistent error handling.
5. Document one-shot and interactive usage.

#### MVP-001-S002: Expression evaluation

Deliver multi-operation one-shot expressions, parentheses, standard precedence, validation, and automated tests while preserving existing basic arithmetic behavior.

#### MVP-001-S003: Interactive calculator

Deliver interactive mode launched by `python -m calculator`, repeated expression evaluation, `Ans` for the previous successful result, `quit` to exit, session-safe errors, tests, and documentation.

### MVP 2 delivery slices

#### MVP-002-S001: GUI foundation

Select and configure a lightweight GUI toolkit, build the calculator layout and display, connect GUI actions to the shared calculation engine, add input-state and error handling, and document launch instructions.

#### MVP-002-S002: Styling and UX polish

Improve visual hierarchy, spacing, typography, button states, keyboard usability, focus behavior, and responsive layout without changing calculation semantics.

#### MVP-002-S003: Calculation history

Show completed calculations in a session-local history view with clear behavior, bounded memory use, and no persistence requirement.

#### MVP-002-S004: Scientific functions

Add an explicitly defined, testable set of scientific operations while preserving basic arithmetic, precedence, error handling, and the shared engine boundary.

#### MVP-002-S005: Packaging and distribution

Provide documented packaging and local distribution artifacts for supported platforms, with reproducible build commands and no embedded secrets or production deployment.

## 10. Risks and mitigations

- **Expression parsing becomes ambiguous:** start with two operands and one operator; defer chained expressions.
- **GUI and engine logic become coupled:** enforce a UI-independent calculation module.
- **Floating-point results surprise users:** document numeric behavior and define expected precision in tests.
- **Toolkit availability varies by platform:** choose a broadly supported toolkit and document platform assumptions.

## 11. Future considerations

- Calculation history
- Keyboard shortcuts
- Chained expressions and parentheses
- Scientific operations
- Configurable number formatting
- Packaging as a desktop executable
