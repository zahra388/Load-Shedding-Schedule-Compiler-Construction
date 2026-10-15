"""
Lexical Analyzer (Lexer) for LoadSheddingLang using PLY (ply.lex).
JUW Compiler Construction Lab Project.

Roman Urdu Explanation for Viva:
Lexer (Scanner) source code ko character by character parhta hai aur meaningful units
(Tokens) mein convert karta hai. Yeh reserved keywords (English aur Roman Urdu dono),
identifiers, numbers, percentages (jaise 18%), aur time (jaise 08:00) ko pehchanta hai.
Agar koi ghair-qanooni character aye toh crash hone ke bajaye error report karke agay barhta hai.
"""

import sys
import os

# Add local ply if available
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import ply.lex as lex
except ImportError:
    from . import ply
    import ply.lex as lex

# Reserved words dictionary: maps both English and Roman Urdu keywords to token names
RESERVED = {
    # English keywords
    'feeder': 'FEEDER',
    'group': 'GROUP',
    'exempt': 'EXEMPT',
    'block': 'BLOCK',
    'start': 'START',
    'end': 'END',
    'slot': 'SLOT',
    'rotation': 'ROTATION',
    'loss': 'LOSS',
    'max': 'MAX',
    'weekday': 'WEEKDAY',
    'weekend': 'WEEKEND',
    'compile': 'COMPILE',
    'hours': 'HOURS',
    'hour': 'HOURS',

    # Roman Urdu keywords (JUW lab syllabus)
    'giroh': 'GROUP',
    'mustasna': 'EXEMPT',
    'shuru': 'START',
    'khatam': 'END',
    'waqfa': 'SLOT',
    'bari': 'ROTATION',
    'nuqsan': 'LOSS',
    'zyada_se_zyada': 'MAX',
    'hafta_war': 'WEEKDAY',
    'hafta_akhir': 'WEEKEND',
    'tayar_karo': 'COMPILE',
    'ghantay': 'HOURS',
    'ghanta': 'HOURS'
}

# List of token names
tokens = [
    'IDENTIFIER',
    'NUMBER',
    'PERCENT',
    'TIME',
    'SEMICOLON',
    'COMMA',
    'LBRACKET',
    'RBRACKET'
] + sorted(list(set(RESERVED.values())))

# Regular expressions for simple tokens
t_SEMICOLON = r';'
t_COMMA     = r','
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'

# Ignored characters: spaces and tabs
t_ignore = ' \t\r'

# Comments: // until the end of line
def t_COMMENT(t):
    r'//[^\n]*'
    pass  # Ignore comments

# Time token: e.g. 08:00, 16:00, 23:59 (must be defined before IDENTIFIER or NUMBER)
def t_TIME(t):
    r'\b\d{1,2}:\d{2}\b'
    t.value = t.value.strip()
    return t

# Percentage token: e.g. 18%, 35%, 0% (single token as required)
def t_PERCENT(t):
    r'\b\d+(\.\d+)?%'
    # Extract numeric portion
    num_str = t.value[:-1]
    t.value = float(num_str) if '.' in num_str else int(num_str)
    return t

# Identifier or keyword
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Check if keyword (case-insensitive for keywords)
    lower_val = t.value.lower()
    if lower_val in RESERVED:
        t.type = RESERVED[lower_val]
    else:
        t.type = 'IDENTIFIER'
    return t

# Number token: integer
def t_NUMBER(t):
    r'\b\d+\b'
    t.value = int(t.value)
    return t

# Track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Error handling rule
def t_error(t):
    char = t.value[0]
    msg = f"Lexical error (line {t.lexer.lineno}): unrecognized or illegal character '{char}'. Remove or replace this invalid character."
    if hasattr(t.lexer, 'errors'):
        t.lexer.errors.append(msg)
    else:
        print(msg, file=sys.stderr)
    t.lexer.skip(1)

def build_lexer():
    """Build and return a fresh PLY lexer instance."""
    lexer = lex.lex(debug=False)
    lexer.errors = []
    return lexer

def tokenize(source_code):
    """
    Tokenizes input source code.
    Returns: (token_list, error_list)
    """
    lexer = build_lexer()
    lexer.lineno = 1
    lexer.errors = []
    lexer.input(source_code)
    
    token_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        token_list.append(tok)
        
    return token_list, lexer.errors

def format_tokens(token_list):
    """Formats token list for display under === TOKENS ===."""
    lines = []
    for tok in token_list:
        lines.append(f"Line {tok.lineno:3d} | Type: {tok.type:<15} | Value: {repr(tok.value)}")
    return "\n".join(lines)
