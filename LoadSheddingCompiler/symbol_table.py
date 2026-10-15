"""
Symbol Table for LoadSheddingLang.
JUW Compiler Construction Lab Project.

Roman Urdu Explanation for Viva:
Symbol Table compiler ka ek central data structure hota hai jo identifiers
(jaise Feeders, Groups, Blocks, Exemptions) aur unke attributes (line loss, max hours, line number, scope)
ko store karta hai. Yeh duplicate definitions detect karne aur semantic checks mein use hota hai.
"""

class SymbolEntry:
    """Represents a single symbol table record."""
    def __init__(self, name, kind, data_type, value, lineno, scope="GLOBAL"):
        self.name = name          # e.g. "Gulberg", "A", "Weekday"
        self.kind = kind          # "FEEDER", "GROUP", "EXEMPTION", "BLOCK"
        self.data_type = data_type  # e.g. "FeederDecl", "GroupRef", "ScheduleBlock"
        self.value = value        # Details / Dict / String representation
        self.lineno = lineno      # Source line number
        self.scope = scope        # Scope name (e.g. "GLOBAL", "BLOCK:Weekday")

    def to_dict(self):
        return {
            "name": self.name,
            "kind": self.kind,
            "type": self.data_type,
            "value": str(self.value),
            "lineno": self.lineno,
            "scope": self.scope
        }


class SymbolTable:
    """Symbol Table managing symbols across scopes."""
    def __init__(self):
        self.entries = []
        # Keyed index by (name, kind, scope)
        self._lookup = {}

    def insert(self, name, kind, data_type, value, lineno, scope="GLOBAL"):
        entry = SymbolEntry(name, kind, data_type, value, lineno, scope)
        self.entries.append(entry)
        key = (name.lower(), kind.upper(), scope.upper())
        self._lookup[key] = entry
        return entry

    def lookup(self, name, kind=None, scope="GLOBAL"):
        """Look up symbol by name, optional kind, and scope."""
        name_lower = name.lower()
        scope_upper = scope.upper()
        if kind:
            key = (name_lower, kind.upper(), scope_upper)
            return self._lookup.get(key)
        for k, entry in self._lookup.items():
            if k[0] == name_lower and k[2] == scope_upper:
                return entry
        return None

    def get_by_kind(self, kind):
        """Returns all entries matching a given kind."""
        kind_upper = kind.upper()
        return [e for e in self.entries if e.kind.upper() == kind_upper]

    def format_table(self):
        """Format the symbol table under === SYMBOL TABLE ===."""
        if not self.entries:
            return "Symbol Table is empty."

        headers = ["NAME", "KIND", "TYPE / UNIT", "LINE", "SCOPE", "ATTRIBUTES / VALUE"]
        widths = [16, 12, 14, 6, 16, 36]

        header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
        sep_line = "-+-".join("-" * w for w in widths)

        lines = [header_line, sep_line]
        for e in self.entries:
            val_str = str(e.value)
            if len(val_str) > widths[5]:
                val_str = val_str[:widths[5] - 3] + "..."
            row = [
                f"{e.name:<{widths[0]}}",
                f"{e.kind:<{widths[1]}}",
                f"{e.data_type:<{widths[2]}}",
                f"{str(e.lineno):<{widths[3]}}",
                f"{e.scope:<{widths[4]}}",
                f"{val_str:<{widths[5]}}"
            ]
            lines.append(" | ".join(row))

        return "\n".join(lines)


def build_symbol_table(ast_root):
    """
    Constructs the Symbol Table from AST.
    Returns: (symbol_table, errors)
    """
    symtab = SymbolTable()
    errors = []

    if not ast_root or not hasattr(ast_root, 'statements'):
        return symtab, errors

    from ast_nodes import FeederNode, ExemptNode, ScheduleBlockNode

    for stmt in ast_root.statements:
        if isinstance(stmt, FeederNode):
            # Check duplicate feeder definition in symbol table
            existing = symtab.lookup(stmt.name, kind="FEEDER")
            if existing:
                errors.append(
                    f"Semantic error (line {stmt.lineno}): duplicate feeder '{stmt.name}' already defined at line {existing.lineno}. Every feeder must have a unique name."
                )
            else:
                val = f"loss={stmt.loss}%, group={stmt.group}, max={stmt.max_hours}h"
                symtab.insert(stmt.name, "FEEDER", "FeederDecl", val, stmt.lineno, "GLOBAL")
                
                # Also track group in symbol table
                grp_entry = symtab.lookup(stmt.group, kind="GROUP")
                if not grp_entry:
                    symtab.insert(stmt.group, "GROUP", "GroupRef", f"feeders=[{stmt.name}]", stmt.lineno, "GLOBAL")
                else:
                    # Update group list
                    grp_entry.value = grp_entry.value.rstrip("]") + f", {stmt.name}]"

        elif isinstance(stmt, ExemptNode):
            val = f"exempted=True, target_feeder={stmt.feeder_name}"
            symtab.insert(stmt.feeder_name, "EXEMPTION", "ExemptionDecl", val, stmt.lineno, "GLOBAL")

        elif isinstance(stmt, ScheduleBlockNode):
            existing_block = symtab.lookup(stmt.name, kind="BLOCK")
            if existing_block:
                errors.append(
                    f"Semantic error (line {stmt.lineno}): duplicate schedule block '{stmt.name}' already defined at line {existing_block.lineno}. Block names must be unique."
                )
            else:
                rot_str = ", ".join(stmt.rotation)
                val = f"{stmt.start_time}-{stmt.end_time}, slot={stmt.slot_hours}h, rot=[{rot_str}]"
                symtab.insert(stmt.name, "BLOCK", "ScheduleBlock", val, stmt.lineno, "GLOBAL")

    return symtab, errors
