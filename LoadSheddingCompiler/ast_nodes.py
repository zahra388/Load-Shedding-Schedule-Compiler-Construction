"""
AST (Abstract Syntax Tree) Node Definitions for LoadSheddingLang.
JUW Compiler Construction Lab Project.

Roman Urdu Explanation for Viva:
AST (Abstract Syntax Tree) syntax analysis ke baad banta hai. Parser raw tokens ko
ek structured tree mein convert karta hai jo program ka semantic meaning represent karti hai.
Har node ek grammar construct ko represent karta hai jaise FeederNode, ExemptNode, aur ScheduleBlockNode.
"""

class ASTNode:
    """Base class for all AST nodes."""
    def __init__(self, lineno=1):
        self.lineno = lineno

    def to_dict(self):
        """Serialize node to dictionary for web UI inspection."""
        res = {"type": self.__class__.__name__, "lineno": self.lineno}
        for k, v in self.__dict__.items():
            if k.startswith("_") or k == "lineno":
                continue
            if isinstance(v, ASTNode):
                res[k] = v.to_dict()
            elif isinstance(v, list):
                res[k] = [item.to_dict() if isinstance(item, ASTNode) else item for item in v]
            else:
                res[k] = v
        return res

    def pretty_print(self, indent=0):
        """Format the AST nicely for display under === AST ===."""
        prefix = "  " * indent
        lines = [f"{prefix}{self.__class__.__name__} (line {self.lineno})"]
        for k, v in self.__dict__.items():
            if k.startswith("_") or k == "lineno":
                continue
            if isinstance(v, ASTNode):
                lines.append(f"{prefix}  {k}:")
                lines.append(v.pretty_print(indent + 2))
            elif isinstance(v, list):
                lines.append(f"{prefix}  {k}: [")
                for item in v:
                    if isinstance(item, ASTNode):
                        lines.append(item.pretty_print(indent + 2))
                    else:
                        lines.append(f"{prefix}    {item}")
                lines.append(f"{prefix}  ]")
            else:
                lines.append(f"{prefix}  {k} = {repr(v)}")
        return "\n".join(lines)


class ProgramNode(ASTNode):
    """Root node containing all top-level statements."""
    def __init__(self, statements, lineno=1):
        super().__init__(lineno)
        self.statements = statements or []

    def pretty_print(self, indent=0):
        prefix = "  " * indent
        lines = [f"{prefix}ProgramNode:"]
        for stmt in self.statements:
            if isinstance(stmt, ASTNode):
                lines.append(stmt.pretty_print(indent + 1))
            else:
                lines.append(f"{prefix}  {repr(stmt)}")
        return "\n".join(lines)


class FeederNode(ASTNode):
    """Represents a feeder definition statement."""
    def __init__(self, name, loss, group, max_hours, lineno=1):
        super().__init__(lineno)
        self.name = name
        self.loss = loss  # float or int percentage (e.g. 18.0)
        self.group = group  # string group name (e.g. 'A')
        self.max_hours = max_hours  # int maximum permitted hours (e.g. 4)


class ExemptNode(ASTNode):
    """Represents an exemption statement for a feeder (e.g. hospital)."""
    def __init__(self, feeder_name, lineno=1):
        super().__init__(lineno)
        self.feeder_name = feeder_name


class ScheduleBlockNode(ASTNode):
    """Represents a schedule block (weekday, weekend, or custom)."""
    def __init__(self, name, block_type, start_time, end_time, slot_hours, rotation, lineno=1):
        super().__init__(lineno)
        self.name = name  # e.g. "Weekday"
        self.block_type = block_type  # "weekday", "weekend", or "custom"
        self.start_time = start_time  # string "08:00"
        self.end_time = end_time      # string "16:00"
        self.slot_hours = slot_hours  # int or float (e.g. 2)
        self.rotation = rotation      # list of group names, e.g. ['A', 'B']


class TimeRangeNode(ASTNode):
    """Represents start and end time pair."""
    def __init__(self, start_time, end_time, lineno=1):
        super().__init__(lineno)
        self.start_time = start_time
        self.end_time = end_time


class RotationNode(ASTNode):
    """Represents group rotation order."""
    def __init__(self, groups, lineno=1):
        super().__init__(lineno)
        self.groups = groups


class CompileNode(ASTNode):
    """Represents an explicit compile / tayar_karo statement."""
    def __init__(self, lineno=1):
        super().__init__(lineno)
