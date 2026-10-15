"""
Syntax Analyzer (Parser) for LoadSheddingLang using PLY (ply.yacc).
JUW Compiler Construction Lab Project.

Roman Urdu Explanation for Viva:
Parser tokens ki sequence ko check karta hai ke woh language ki Context-Free Grammar (CFG)
ke mutabiq hain ya nahi. Agar koi syntax galat ho (jaise semicolon missing ya galat keyword),
toh syntax error generate hota hai. Humne 'error' token use kiya hai taake parser crash na ho
aur aik se zyada independent errors ko ek hi compilation run mein report kar sake.
"""

import sys
import os

# Add local directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import ply.yacc as yacc
except ImportError:
    from . import ply
    import ply.yacc as yacc

from lexer import tokens
from ast_nodes import (
    ProgramNode,
    FeederNode,
    ExemptNode,
    ScheduleBlockNode,
    CompileNode
)

class ParserState:
    def __init__(self):
        self.errors = []
        self.last_error_line = -1

# Global state tracker for parser run
_parser_state = ParserState()

# Grammar rules

def p_program(p):
    '''program : statement_list
               | empty'''
    if p[1] is None:
        p[0] = ProgramNode([], lineno=1)
    else:
        # Filter out None from error recovery
        valid_stmts = [s for s in p[1] if s is not None]
        lineno = valid_stmts[0].lineno if valid_stmts else 1
        p[0] = ProgramNode(valid_stmts, lineno=lineno)

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# Error recovery rule for statements ending in semicolon
def p_statement_error(p):
    '''statement : error SEMICOLON'''
    # Error already recorded in p_error; recover after semicolon
    p[0] = None

# Feeder statement with loss, group, max hours
def p_statement_feeder_full(p):
    '''statement : FEEDER IDENTIFIER loss_opt GROUP IDENTIFIER max_opt SEMICOLON'''
    lineno = p.lineno(1)
    feeder_name = p[2]
    loss = p[3]
    group_name = p[5]
    max_h = p[6]
    p[0] = FeederNode(feeder_name, loss, group_name, max_h, lineno=lineno)

def p_loss_opt(p):
    '''loss_opt : LOSS PERCENT
                | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = 0.0

def p_max_opt(p):
    '''max_opt : MAX NUMBER HOURS
               | MAX NUMBER
               | empty'''
    if len(p) >= 3:
        p[0] = p[2]
    else:
        p[0] = 24  # default maximum if unspecified

# Exempt statement
def p_statement_exempt_with_feeder_kw(p):
    '''statement : EXEMPT FEEDER IDENTIFIER SEMICOLON
                 | EXEMPT IDENTIFIER SEMICOLON'''
    lineno = p.lineno(1)
    if len(p) == 5:
        p[0] = ExemptNode(p[3], lineno=lineno)
    else:
        p[0] = ExemptNode(p[2], lineno=lineno)

# Schedule block statement
def p_statement_block(p):
    '''statement : BLOCK block_name START TIME END TIME SLOT NUMBER hours_opt ROTATION rotation_groups SEMICOLON
                 | WEEKDAY BLOCK block_name_opt START TIME END TIME SLOT NUMBER hours_opt ROTATION rotation_groups SEMICOLON
                 | WEEKEND BLOCK block_name_opt START TIME END TIME SLOT NUMBER hours_opt ROTATION rotation_groups SEMICOLON
                 | BLOCK WEEKDAY block_name_opt START TIME END TIME SLOT NUMBER hours_opt ROTATION rotation_groups SEMICOLON
                 | BLOCK WEEKEND block_name_opt START TIME END TIME SLOT NUMBER hours_opt ROTATION rotation_groups SEMICOLON'''
    lineno = p.lineno(1)
    # Extract values based on rule structure
    rule_words = [str(x).lower() for x in p[1:4]]
    if 'weekend' in rule_words:
        block_type = 'weekend'
    elif 'weekday' in rule_words:
        block_type = 'weekday'
    else:
        block_type = 'custom'

    if len(p) == 13:
        # Standard: BLOCK block_name START ...
        name = p[2]
        start_time = p[4]
        end_time = p[6]
        slot_hours = p[8]
        rotation = p[11]
    else:
        # With modifier
        name = p[3] if p[3] else (block_type.capitalize() if block_type != 'custom' else 'Schedule')
        start_time = p[5]
        end_time = p[7]
        slot_hours = p[9]
        rotation = p[12]

    p[0] = ScheduleBlockNode(name, block_type, start_time, end_time, slot_hours, rotation, lineno=lineno)

def p_block_name(p):
    '''block_name : IDENTIFIER
                  | WEEKDAY
                  | WEEKEND'''
    p[0] = str(p[1])

def p_block_name_opt(p):
    '''block_name_opt : block_name
                      | empty'''
    p[0] = p[1]

def p_hours_opt(p):
    '''hours_opt : HOURS
                 | empty'''
    pass

def p_rotation_groups(p):
    '''rotation_groups : group_sequence
                       | LBRACKET group_sequence RBRACKET'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_group_sequence(p):
    '''group_sequence : group_sequence COMMA IDENTIFIER
                      | group_sequence IDENTIFIER
                      | IDENTIFIER'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    elif len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# Compile statement
def p_statement_compile(p):
    '''statement : COMPILE SEMICOLON'''
    p[0] = CompileNode(lineno=p.lineno(1))

def p_empty(p):
    '''empty :'''
    p[0] = None

# Syntax error handler
def p_error(p):
    global _parser_state
    if p:
        line = p.lineno
        # Avoid duplicate error on same line if already recorded
        if line != _parser_state.last_error_line:
            val = p.value
            err_msg = f"Syntax error (line {line}): unexpected '{val}' (token type: {p.type}). Check statement syntax and verify ending semicolon ';'."
            _parser_state.errors.append(err_msg)
            _parser_state.last_error_line = line
    else:
        err_msg = f"Syntax error (line {_parser_state.last_error_line + 1 if _parser_state.last_error_line > 0 else 1}): unexpected end of file. Ensure all statements end with a semicolon ';' and blocks are closed."
        _parser_state.errors.append(err_msg)


def build_parser():
    """Build and return a fresh PLY parser instance with write_tables=False."""
    return yacc.yacc(debug=False, write_tables=False)

def parse(source_code, lexer=None):
    """
    Parses source code into an AST.
    Returns: (ast_root, error_list)
    """
    global _parser_state
    _parser_state = ParserState()

    from lexer import build_lexer
    if lexer is None:
        lexer = build_lexer()
        lexer.lineno = 1
        lexer.errors = []

    parser = build_parser()
    ast = parser.parse(source_code, lexer=lexer, tracking=True)

    # Return AST and any parser errors
    return ast, _parser_state.errors
