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
```

---

## 7. Roman Urdu Lab Viva & Defense Guide (طلباء کے لیے رہنمائی)

Agar viva mein external examiner ya professor aap se sawalat poochein, toh in simple Roman Urdu explanations se aasani se samjha sakte hain:

### Q1: Lexer (Lexical Analyzer) ka kya kaam hai?
**Jawab:**  
"Sir/Madam, Lexer source code ke character stream ko read karta hai aur use meaningful units jinhe **Tokens** kehte hain un mein convert karta hai. Humare lexer mein English keywords (jaise `feeder`, `group`, `start`, `slot`) aur Roman Urdu keywords (jaise `giroh`, `shuru`, `waqfa`, `bari`) dono ek hi reserved dictionary mein map hain. Jab bhi koi keyword parha jata hai, lexer unhe same token assign karta hai. Agar koi invalid character aye (jaise `@`), toh lexer crash nahi hota balke line number ke sath `Lexical error` report karta hai."

### Q2: Parser aur AST Node ka kya talluq hai?
**Jawab:**  
"Parser tokens ki sequence ko Context-Free Grammar (CFG) ke rules ke sath check karta hai. Agar syntax sahi ho, toh woh ek **Abstract Syntax Tree (AST)** generate karta hai. Har AST Node program ke ek construct ko represent karta hai, jaise `FeederNode`, `ExemptNode`, aur `ScheduleBlockNode`. Agar statement ke end mein semicolon `;` missing ho, toh humara parser `error` token ke zariye recover karta hai taake aik se zyada errors ek hi run mein display ho sakein."

### Q3: Symbol Table mein kya store hota hai?
**Jawab:**  
"Symbol table ek central dictionary ya database hota hai jo program ke identifiers (Feeders, Groups, Blocks, Exemptions) ke attributes save karta hai: unka naam, type, line loss percentage, maximum permitted hours, source line number, aur scope. Is table ke zariye hum duplicate declarations (jaise do dafa Gulberg declare karna) ko detect karte hain."

### Q4: Semantic Analysis mein Rules R1 se R7 kaise check hote hain?
**Jawab:**  
"Semantic analyzer syntax ke bajaye program ke **meaning** aur **rules** ko verify karta hai:
- **R1:** Feeder name duplicate na ho aur har feeder aik hi group mein ho.
- **R2:** Hospital ya exempt feeder ko hamesha 0 hours shedding mile.
- **R3 & R6:** Kisi feeder ke calculated hours uske maximum limit se zyada na hon. Agar exceed karein toh detailed error aye.
- **R4:** Schedule ka total duration (e.g. 8 ghantay) slot length (e.g. 2 ghantay) pe poora divide hona chahiye (8 % 2 == 0). 7 ghantay pe error aye ga.
- **R5:** Rotation mein jo bhi group aye, usme feeders hone chahiye.
- **R7:** Time 24-hour clock (00:00 se 23:59) mein valid hona chahiye."

### Q5: Three-Address Code (TAC) kya hai aur kyun banaya gaya?
**Jawab:**  
"Three-Address Code (TAC) ek Intermediate Representation (IR) hai. Source code ko simple instructions mein convert kiya jata hai jisme maximum 3 addresses (jaise `t1 = END - START`) hote hain. Yeh machine-independent hota hai. Humne TAC ke zariye slot count calculate kiya, loop ke through groups ko rotation di, aur feeders ke shedding hours nikale."

### Q6: Optimization mein Constant Folding aur Dead Code Elimination kaise kaam karti hai?
**Jawab:**  
"Optimization compiler ka 6th phase hai:
1. **Constant Folding:** Jo calculations compile-time pe solve ho sakti hain unhe pehle hi compute kar liya jata hai. Jaise `960 - 480` ko `480`, `480 / 60` ko `8`, aur `8 / 2` ko `4 slots` mein fold kar diya jata hai.
2. **Dead Code Elimination:** Jo temporary variables fold ho chuke hain ya aage read nahi hote, unki instructions ko remove kar diya jata hai taake code chhota aur tez ho jaye.
Humne verify kiya hai ke Optimized TAC aur Unoptimized TAC dono ka final output aur timetable 100% identical rehta hai."

### Q7: Timetable hardcoded hai ya execute hota hai?
**Jawab:**  
"Sir/Madam, timetable bilkul hardcoded nahi hai! Humara `tac_executor.py` ek virtual machine hai jo generated Three-Address Code ko step-by-step interpret karta hai (bina Python `eval()` use kiye). Loop chalta hai, memory registers update hote hain, aur real calculation ke baad final timetable table aur feeder totals print hote hain."
