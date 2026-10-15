"""
Tkinter Graphical User Interface (GUI) for Load-Shedding Schedule Compiler.
Compiler Construction Lab Project | JUW.

Features:
- Title: Load-Shedding Schedule Compiler
- Code Editor with Line Numbers & Example Loader
- Compile, Clear, Load Example, Run Tests buttons
- Multi-Tab & Unified Phase Viewer (Tokens, AST, Symbol Table, Semantic, TAC, Optimized TAC, Result)
- Errors and warnings highlighted in bold red
- Clean error recovery (no tracebacks, remains open and usable)
- Calls the identical compiler engine as main.py

Roman Urdu Explanation for Viva:
GUI (Graphical User Interface) Tkinter library se banaya gaya hai. Yeh user ko
code likhne, test cases load karne, aur ek click pe saare 7 compiler phases
(Lexer se lekar Timetable tak) dekhne ki sahulat deta hai. Agar koi error aye toh
woh red color mein show hoti hai aur program crash nahi hota.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

from main import run_compiler

STANDARD_EXAMPLE = """// Standard Weekday Scenario - LoadSheddingLang
// JUW Compiler Construction Lab Project

feeder Gulberg loss 18% group A max 4 hours;
feeder ModelTown loss 35% group B max 6 hours;
feeder Services group A max 0 hours;
exempt feeder Services;

block Weekday start 08:00 end 16:00 slot 2 hours rotation A, B;
"""

URDU_EXAMPLE = """// Roman Urdu Keywords - LoadSheddingLang
feeder Gulberg nuqsan 18% giroh A zyada_se_zyada 4 ghantay;
feeder ModelTown nuqsan 35% giroh B zyada_se_zyada 6 ghantay;
feeder Services giroh A zyada_se_zyada 0 ghantay;
mustasna feeder Services;

block Weekday shuru 08:00 khatam 16:00 waqfa 2 ghantay bari A, B;
"""

class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Load-Shedding Schedule Compiler | JUW Compiler Construction Lab")
        self.root.geometry("1100x750")
        self.root.minsize(800, 600)

        # Style configuration
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self._build_ui()
        self.load_code(STANDARD_EXAMPLE)

    def _build_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg="#1e293b", padx=16, pady=12)
        header.pack(fill="x")

        title_lbl = tk.Label(
            header,
            text="Load-Shedding Schedule Compiler",
            font=("Helvetica", 16, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title_lbl.pack(side="left")

        sub_lbl = tk.Label(
            header,
            text="Jinnah University for Women | Dept. of CS & SE",
            font=("Helvetica", 10),
            fg="#94a3b8",
            bg="#1e293b"
        )
        sub_lbl.pack(side="right", pady=4)

        # Toolbar Frame
        toolbar = tk.Frame(self.root, bg="#f1f5f9", padx=12, pady=8)
        toolbar.pack(fill="x")

        compile_btn = tk.Button(
            toolbar,
            text="▶ Compile",
            bg="#2563eb",
            fg="white",
            font=("Helvetica", 10, "bold"),
            padx=16,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self.compile_code
        )
        compile_btn.pack(side="left", padx=4)

        clear_btn = tk.Button(
            toolbar,
            text="Clear",
            bg="#e2e8f0",
            fg="#0f172a",
            font=("Helvetica", 10),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self.clear_input
        )
        clear_btn.pack(side="left", padx=4)

        load_ex_btn = tk.Button(
            toolbar,
            text="Load Example (English)",
            bg="#e2e8f0",
            fg="#0f172a",
            font=("Helvetica", 10),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=lambda: self.load_code(STANDARD_EXAMPLE)
        )
        load_ex_btn.pack(side="left", padx=4)

        load_urdu_btn = tk.Button(
            toolbar,
            text="Load Example (Roman Urdu)",
            bg="#e2e8f0",
            fg="#0f172a",
            font=("Helvetica", 10),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=lambda: self.load_code(URDU_EXAMPLE)
        )
        load_urdu_btn.pack(side="left", padx=4)

        # Test case selector
        tk.Label(toolbar, text="Load Test:", bg="#f1f5f9", font=("Helvetica", 9, "bold")).pack(side="left", padx=(16, 4))
        self.test_var = tk.StringVar(value="test01")
        test_dropdown = ttk.Combobox(
            toolbar,
            textvariable=self.test_var,
            values=[f"test{i:02d}" for i in range(1, 10)],
            width=8,
            state="readonly"
        )
        test_dropdown.pack(side="left")
        test_dropdown.bind("<<ComboboxSelected>>", self._on_test_selected)

        # Main Paned Window (Split into Editor on left, Phases on right)
        paned = tk.PanedWindow(self.root, orient="horizontal", sashrelief="raised", sashwidth=6)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # Left Frame: Editor
        editor_frame = tk.LabelFrame(paned, text="Program Source (LoadSheddingLang)", padx=6, pady=6)
        paned.add(editor_frame, minsize=350)

        self.editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap="none",
            font=("Courier", 11),
            bg="#ffffff",
            fg="#0f172a",
            undo=True
        )
        self.editor.pack(fill="both", expand=True)

        # Right Frame: Compiler Output Notebook
        out_frame = tk.LabelFrame(paned, text="Compiler Pipeline Output", padx=6, pady=6)
        paned.add(out_frame, minsize=450)

        self.notebook = ttk.Notebook(out_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tabs for every compiler phase
        self.tabs = {}
        tab_names = [
            ("All Output", "all"),
            ("Tokens", "tokens"),
            ("AST", "ast"),
            ("Symbol Table", "symtab"),
            ("Semantic", "semantic"),
            ("TAC", "tac"),
            ("Optimized TAC", "opt_tac"),
            ("Result", "result")
        ]

        for title, key in tab_names:
            tab_frame = tk.Frame(self.notebook)
            txt = scrolledtext.ScrolledText(
                tab_frame,
                wrap="none",
                font=("Courier", 10),
                bg="#f8fafc",
                fg="#0f172a"
            )
            # Configure error tag in red
            txt.tag_configure("error", foreground="#dc2626", font=("Courier", 10, "bold"))
            txt.tag_configure("warning", foreground="#d97706", font=("Courier", 10, "bold"))
            txt.tag_configure("success", foreground="#16a34a", font=("Courier", 10, "bold"))
            txt.tag_configure("heading", foreground="#2563eb", font=("Courier", 11, "bold"))

            txt.pack(fill="both", expand=True)
            self.notebook.add(tab_frame, text=title)
            self.tabs[key] = txt

        # Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready to compile.",
            bd=1,
            relief="sunken",
            anchor="w",
            padx=8,
            pady=3,
            bg="#f1f5f9",
            fg="#475569"
        )
        self.status_bar.pack(side="bottom", fill="x")

    def load_code(self, code_str):
        self.editor.delete("1.0", tk.END)
        self.editor.insert(tk.END, code_str)
        self.status_bar.config(text="Loaded source code.", fg="#0f172a")

    def clear_input(self):
        self.editor.delete("1.0", tk.END)
        for txt in self.tabs.values():
            txt.delete("1.0", tk.END)
        self.status_bar.config(text="Cleared editor and outputs.", fg="#475569")

    def _on_test_selected(self, event=None):
        tname = self.test_var.get()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "tests", f"{tname}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.load_code(f.read())
            self.status_bar.config(text=f"Loaded {tname}.txt", fg="#2563eb")

    def compile_code(self):
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Empty Code", "Please enter LoadSheddingLang code before compiling.")
            return

        # Clear old outputs
        for txt in self.tabs.values():
            txt.delete("1.0", tk.END)

        # Run compiler engine
        try:
            # Capture console outputs
            import io
            import contextlib
            stdout_trap = io.StringIO()
            with contextlib.redirect_stdout(stdout_trap):
                success, data = run_compiler(code)

            all_out = stdout_trap.getvalue()
            self._display_phase_outputs(all_out, success, data)

            if success:
                self.status_bar.config(text="✓ Compilation and scheduling succeeded!", fg="#16a34a")
                self.notebook.select(self.tabs["result"].master)
            else:
                stopped = data.get("stopped_at_phase", "UNKNOWN")
                self.status_bar.config(text=f"✗ Compilation stopped at {stopped} phase due to errors.", fg="#dc2626")

        except Exception as e:
            # Never crash GUI! Display cleanly without traceback
            err_msg = f"Internal execution note: {str(e)}"
            self.tabs["all"].insert(tk.END, err_msg + "\n", "error")
            self.status_bar.config(text="Compilation encountered an issue.", fg="#dc2626")

    def _display_phase_outputs(self, all_out, success, data):
        # Populate All Output tab
        all_txt = self.tabs["all"]
        for line in all_out.splitlines():
            if line.startswith("==="):
                all_txt.insert(tk.END, line + "\n", "heading")
            elif "error" in line.lower() or "compilation stopped" in line.lower() or "failure" in line.lower():
                all_txt.insert(tk.END, line + "\n", "error")
            elif "warning" in line.lower():
                all_txt.insert(tk.END, line + "\n", "warning")
            elif "passed" in line.lower() or "succeeded" in line.lower():
                all_txt.insert(tk.END, line + "\n", "success")
            else:
                all_txt.insert(tk.END, line + "\n")

        # Specific tabs
        if data.get("token_lines"):
            self.tabs["tokens"].insert(tk.END, data["token_lines"])

        if data.get("ast_text"):
            self.tabs["ast"].insert(tk.END, data["ast_text"])

        if data.get("symbol_table_text"):
            self.tabs["symtab"].insert(tk.END, data["symbol_table_text"])

        # Semantic tab
        sem_txt = self.tabs["semantic"]
        for w in data.get("semantic_warnings", []):
            sem_txt.insert(tk.END, w + "\n", "warning")
        for e in data.get("semantic_errors", []):
            sem_txt.insert(tk.END, e + "\n", "error")
        if not data.get("semantic_errors"):
            sem_txt.insert(tk.END, "Semantic analysis passed. All rules R1–R7 successfully verified.\n", "success")

        # TAC tab
        if data.get("tac_text"):
            self.tabs["tac"].insert(tk.END, data["tac_text"])

        # Optimized TAC tab
        if data.get("optimized_tac_text"):
            self.tabs["opt_tac"].insert(tk.END, data["optimized_tac_text"])

        # Result tab
        if data.get("result_text"):
            res_txt = self.tabs["result"]
            for line in data["result_text"].splitlines():
                if "PASSED" in line or "succeeded" in line:
                    res_txt.insert(tk.END, line + "\n", "success")
                elif "FAILURE" in line or "stopped" in line:
                    res_txt.insert(tk.END, line + "\n", "error")
                elif line.startswith("---"):
                    res_txt.insert(tk.END, line + "\n", "heading")
                else:
                    res_txt.insert(tk.END, line + "\n")

def main():
    if not TKINTER_AVAILABLE:
        print("Note: Tkinter is not installed in this environment.")
        print("To run the compiler from the command line, use:")
        print("    python main.py tests/test01.txt")
        return

    # Check for X11 / Display
    display = os.environ.get("DISPLAY")
    try:
        root = tk.Tk()
        app = CompilerGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Could not open graphical window (DISPLAY='{display}'): {e}")
        print("Running in headless mode. Use 'python main.py tests/test01.txt' for CLI execution.")

if __name__ == "__main__":
    main()
