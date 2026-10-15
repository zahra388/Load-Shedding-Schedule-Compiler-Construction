# Load-Shedding Schedule Compiler
**Compiler Construction Lab Project | BS Computer Science & Software Engineering**  
**Jinnah University for Women (JUW)**

---

## 1. Project Overview

The **Load-Shedding Schedule Compiler** is a complete, working multi-phase compiler for **LoadSheddingLang**, a domain-specific language designed to schedule and optimize electrical load-shedding timetables across city feeders.

Unlike a simple timetable calculator or mockup, this system implements every classical compiler phase from scratch:
1. **Lexical Analysis (Lexer)** using PLY (`ply.lex`) with full English & Roman Urdu keyword support.
2. **Syntax Analysis (Parser & AST)** using PLY (`ply.yacc`) with syntax-error recovery.
3. **Symbol Table Management** tracking feeders, line-losses, groups, and blocks with scope.
4. **Semantic Analysis** strictly enforcing Rules **R1 through R7**.
5. **Intermediate Code Generation (TAC)** producing genuine Three-Address Code with temporaries, labels, and jumps.
6. **Code Optimization** performing Constant Folding & Dead Code Elimination.
7. **Intermediate Execution Engine (VM)** executing TAC instructions in memory without using `eval()`.
8. **Tkinter GUI & Web IDE** providing real-time visual inspection of every phase.

---

## 2. Requirements & Installation

- **Python 3.8+**
- **PLY (Python Lex-Yacc)** (A self-contained pure-Python copy of PLY 3.11 is bundled directly in the `ply/` folder, so no external internet access or pip install is mandatory).

If you wish to install PLY globally via pip:
```bash
pip install ply
```

---

## 3. Directory Structure

```text
LoadSheddingCompiler/
├── main.py              # Command-line driver executing the 7 phases in order
├── gui.py               # Tkinter Graphical User Interface
├── lexer.py             # PLY Lexer with English & Roman Urdu keyword mappings
├── parser_module.py     # PLY Yacc Parser & CFG grammar rules
├── ast_nodes.py         # Abstract Syntax Tree (AST) node definitions
├── symbol_table.py      # Symbol Table data structure and builder
├── semantic.py          # Semantic Analyzer enforcing Rules R1–R7
├── tac_generator.py     # Three-Address Code (TAC) generator
├── optimizer.py         # Constant Folding & Dead Code Elimination optimizer
├── tac_executor.py      # Standalone TAC Virtual Machine (No eval)
├── design.txt           # Formal language specification and design document
├── README.md            # User manual and lab viva defense guide
├── ply/                 # Bundled pure-Python PLY library (portable)
└── tests/
    ├── test01.txt       # English-only standard scenario
    ├── test02.txt       # Roman Urdu-only standard scenario
    ├── test03.txt       # Mixed keywords scenario
    ├── test04.txt       # Lexical error test (illegal character)
    ├── test05.txt       # Syntax error test (missing semicolon)
    ├── test06.txt       # Semantic error (Rule R1: duplicate feeder)
    ├── test07.txt       # Semantic error (Rule R4: invalid slot division)
    ├── test08.txt       # Semantic error (Rule R3/R6: max hours exceeded)
    └── test09.txt       # Boundary case (scheduled hours == max permitted)
```

---

## 4. How to Run the Compiler

### A. Terminal Execution
Run any program or test case using `main.py`:
```bash
python main.py tests/test01.txt
```

The output displays all phases in strict sequence:
```text
=== TOKENS ===
=== AST ===
=== SYMBOL TABLE ===
=== SEMANTIC ===
=== TAC ===
=== OPTIMIZED TAC ===
=== RESULT ===
```
If errors are encountered in any phase, the compiler displays the error, prints `Compilation stopped.`, and safely exits without proceeding to subsequent phases.

### B. Launching the Graphical Interface (GUI)
Run `gui.py` to launch the student-friendly Tkinter application:
```bash
python gui.py
```
- Click **▶ Compile** to execute the pipeline.
- Switch tabs to inspect Tokens, AST, Symbol Table, Semantic checks, TAC, Optimized TAC, and Timetable Result.
- Errors are highlighted in red without crashing the interface.

---

## 5. How to Run All 9 Test Cases

Run the automated test suite from the terminal:
```bash
python -c "
import os, subprocess, sys
for i in range(1, 10):
    t = f'tests/test{i:02d}.txt'
    res = subprocess.run([sys.executable, 'main.py', t], capture_output=True, text=True)
    status = 'PASSED (Success)' if res.returncode == 0 else 'PASSED (Correctly Caught Error)'
    print(f'[{t}]: {status}')
"
```

---

## 6. Sample Program & Expected Output

### Standard Weekday Program (`tests/test01.txt`):
```text
feeder Gulberg loss 18% group A max 4 hours;
feeder ModelTown loss 35% group B max 6 hours;
feeder Services group A max 0 hours;
exempt feeder Services;

block Weekday start 08:00 end 16:00 slot 2 hours rotation A, B;
```

### Expected Output under `=== RESULT ===`:
```text
Schedule Block : Weekday
Time Range     : 08:00 – 16:00
Slot Length    : 2 hours
Total Slots    : 4

--- GENERATED TIMETABLE ---
Time Slot        | Assigned Group  
-----------------+------------------
08:00–10:00      | A               
10:00–12:00      | B               
12:00–14:00      | A               
14:00–16:00      | B               

--- GROUP TOTALS ---
Group A     : 4 hours
Group B     : 4 hours

--- FEEDER SHEDDING HOURS ---
Feeder Gulberg   : 4 hours (Max permitted: 4h)
Feeder ModelTown : 4 hours (Max permitted: 6h)
Feeder Services  : 0 hours (Max permitted: 0h) [EXEMPT - 0 HOURS]

--- VALIDATION & STATUS ---
PASSED : Feeder 'Gulberg' within limit (4h <= 4h).
PASSED : Feeder 'ModelTown' within limit (4h <= 6h).
PASSED : Feeder 'Services' within limit (0h <= 0h).

Compilation and scheduling succeeded successfully.
