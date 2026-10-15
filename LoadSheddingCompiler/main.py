"""
Load-Shedding Schedule Compiler - Main CLI Entry Point.
Compiler Construction Lab Project | Jinnah University for Women (JUW)
Department of Computer Science and Software Engineering.

Executes all compiler phases in exact sequence:
=== TOKENS ===
=== AST ===
=== SYMBOL TABLE ===
=== SEMANTIC ===
=== TAC ===
=== OPTIMIZED TAC ===
=== RESULT ===

Usage:
  python main.py tests/test01.txt
"""

import sys
import os

# Add local directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import tokenize, format_tokens
from parser_module import parse
from symbol_table import build_symbol_table
from semantic import SemanticAnalyzer
from tac_generator import TACGenerator
from optimizer import TACOptimizer, format_optimized_tac
from tac_executor import TACExecutionEngine, format_result

def run_compiler(source_code, source_file_name="<input>"):
    """
    Runs the complete compiler pipeline on source_code string.
    Returns: (success: bool, phase_data: dict)
    """
    phase_data = {
        "tokens": None,
        "token_lines": "",
        "ast": None,
        "ast_text": "",
        "symbol_table": None,
        "symbol_table_text": "",
        "semantic_errors": [],
        "semantic_warnings": [],
        "tac_instructions": [],
        "tac_text": "",
        "optimized_tac": [],
        "optimized_tac_text": "",
        "result": None,
        "result_text": "",
        "stopped_at_phase": None,
        "error_messages": []
    }

    # ==================== 1. LEXICAL ANALYSIS ====================
    print("=== TOKENS ===")
    token_list, lex_errors = tokenize(source_code)
    phase_data["tokens"] = token_list
    formatted_tokens = format_tokens(token_list)
    phase_data["token_lines"] = formatted_tokens

    if formatted_tokens:
        print(formatted_tokens)

    if lex_errors:
        for err in lex_errors:
            print(err)
        print("Compilation stopped.")
        phase_data["stopped_at_phase"] = "LEXER"
        phase_data["error_messages"] = lex_errors
        return False, phase_data

    # ==================== 2. SYNTAX ANALYSIS (AST) ====================
    print("=== AST ===")
    ast_root, parse_errors = parse(source_code)
    phase_data["ast"] = ast_root

    if parse_errors:
        for err in parse_errors:
            print(err)
        print("Compilation stopped.")
        phase_data["stopped_at_phase"] = "PARSER"
        phase_data["error_messages"] = parse_errors
        return False, phase_data

    if ast_root:
        ast_str = ast_root.pretty_print()
        phase_data["ast_text"] = ast_str
        print(ast_str)
    else:
        print("Empty AST.")
        print("Compilation stopped.")
        phase_data["stopped_at_phase"] = "PARSER"
        phase_data["error_messages"] = ["Syntax error (line 1): empty program."]
        return False, phase_data

    # ==================== 3. SYMBOL TABLE ====================
    print("=== SYMBOL TABLE ===")
    symtab, sym_errors = build_symbol_table(ast_root)
    phase_data["symbol_table"] = symtab
    sym_text = symtab.format_table()
    phase_data["symbol_table_text"] = sym_text
    print(sym_text)

    if sym_errors:
        for err in sym_errors:
            print(err)
        print("Compilation stopped.")
        phase_data["stopped_at_phase"] = "SYMBOL_TABLE"
        phase_data["error_messages"] = sym_errors
        return False, phase_data

    # ==================== 4. SEMANTIC ANALYSIS ====================
    print("=== SEMANTIC ===")
    analyzer = SemanticAnalyzer()
    sem_success, sem_errors, sem_warnings = analyzer.analyze(ast_root)
    phase_data["semantic_errors"] = sem_errors
    phase_data["semantic_warnings"] = sem_warnings

    for warn in sem_warnings:
        print(warn)

    if not sem_success or sem_errors:
        for err in sem_errors:
            print(err)
        print("Compilation stopped.")
        phase_data["stopped_at_phase"] = "SEMANTIC"
        phase_data["error_messages"] = sem_errors
        return False, phase_data

    print("Semantic analysis passed. All rules R1–R7 successfully verified.")

    # ==================== 5. INTERMEDIATE CODE (TAC) ====================
    print("=== TAC ===")
    tac_gen = TACGenerator()
    tac_instrs = tac_gen.generate(ast_root)
    phase_data["tac_instructions"] = tac_instrs
    tac_str = tac_gen.format_code()
    phase_data["tac_text"] = tac_str
    print(tac_str)

    # ==================== 6. CODE OPTIMIZATION ====================
    print("=== OPTIMIZED TAC ===")
    optimizer = TACOptimizer()
    opt_instrs = optimizer.optimize(tac_instrs)
    phase_data["optimized_tac"] = opt_instrs
    opt_str = format_optimized_tac(opt_instrs)
    phase_data["optimized_tac_text"] = opt_str
    print(opt_str)

    # ==================== 7. TAC EXECUTION & RESULT ====================
    print("=== RESULT ===")
    executor = TACExecutionEngine()
    result = executor.execute(opt_instrs)
    phase_data["result"] = result
    result_str = format_result(result)
    phase_data["result_text"] = result_str
    print(result_str)

    return result["success"], phase_data

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file.txt>")
        print("Example: python main.py tests/test01.txt")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: file '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

    success, _ = run_compiler(code, file_path)
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
