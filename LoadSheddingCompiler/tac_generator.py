"""
Three-Address Code (TAC) Generator for LoadSheddingLang.
JUW Compiler Construction Lab Project.

Generates genuine, executable intermediate representation (IR) including:
- Temporaries (t1, t2, ...)
- Labels (L1, L2, ...)
- Binary operations (-, /, *, +)
- Conditional jumps (IF ... GOTO)
- Slot calculation, rotation loops, exemption logic, and max-hours validation

Roman Urdu Explanation for Viva:
TAC (Three-Address Code) compiler ka Intermediate Representation (IR) hai.
Yeh source code ko simple, machine-independent instructions mein torhta hai
jahan har instruction mein zyada se zyada teen addresses (variables ya constants)
hote hain. Yeh optimization aur machine execution ke darmiyan ka bridge hai.
"""

from ast_nodes import FeederNode, ExemptNode, ScheduleBlockNode
from semantic import parse_time_to_minutes

class TACInstruction:
    """Represents a single Three-Address Code instruction."""
    def __init__(self, op, arg1=None, arg2=None, result=None, comment=None):
        self.op = op          # '=', '+', '-', '*', '/', 'IF', 'GOTO', 'LABEL', 'ASSIGN_SLOT', etc.
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.comment = comment

    def __str__(self):
        if self.op == 'LABEL':
            return f"{self.result}:"
        elif self.op == 'COMMENT':
            return f"; {self.comment}"
        elif self.op == 'GOTO':
            return f"GOTO {self.result}"
        elif self.op == 'IF':
            return f"IF {self.arg1} GOTO {self.result}"
        elif self.op == '=':
            return f"{self.result} = {self.arg1}"
        elif self.op in ('+', '-', '*', '/', '==', '<=', '>=', '<', '>'):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.op == 'ASSIGN_SLOT':
            return f"ASSIGN_SLOT({self.arg1}, {self.arg2})"
        elif self.op == 'CALC_FEEDER_HOURS':
            return f"CALC_FEEDER_HOURS({self.arg1}, {self.arg2})"
        elif self.op == 'APPLY_EXEMPT':
            return f"APPLY_EXEMPT({self.arg1})"
        elif self.op == 'CHECK_MAX_HOURS':
            return f"CHECK_MAX_HOURS({self.arg1}, {self.arg2})"
        else:
            return f"{self.op} {self.arg1 or ''} {self.arg2 or ''} {self.result or ''}".strip()


class TACGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.instructions = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, arg1=None, arg2=None, result=None, comment=None):
        instr = TACInstruction(op, arg1, arg2, result, comment)
        self.instructions.append(instr)
        return instr

    def generate(self, ast_root):
        """
        Generates TAC from AST.
        """
        self.temp_count = 0
        self.label_count = 0
        self.instructions = []

        feeders = {}
        exemptions = set()
        blocks = []

        for stmt in ast_root.statements:
            if isinstance(stmt, FeederNode):
                feeders[stmt.name] = stmt
            elif isinstance(stmt, ExemptNode):
                exemptions.add(stmt.feeder_name)
            elif isinstance(stmt, ScheduleBlockNode):
                blocks.append(stmt)

        self.emit('COMMENT', comment="=== LoadSheddingLang TAC Program ===")
        self.emit('COMMENT', comment="Feeder Declarations")
        for f_name, f in feeders.items():
            self.emit('=', f.loss, result=f"FEEDER_LOSS_{f_name}")
            self.emit('=', f"'{f.group}'", result=f"FEEDER_GROUP_{f_name}")
            self.emit('=', f.max_hours, result=f"FEEDER_MAX_{f_name}")

        self.emit('COMMENT', comment="Exemptions")
        for ex in exemptions:
            self.emit('APPLY_EXEMPT', arg1=ex)

        for block in blocks:
            self._generate_block_tac(block, feeders, exemptions)

        return self.instructions

    def _generate_block_tac(self, block, feeders, exemptions):
        self.emit('COMMENT', comment=f"=== Schedule Block: {block.name} ({block.block_type}) ===")
        start_min, _ = parse_time_to_minutes(block.start_time, block.lineno)
        end_min, _ = parse_time_to_minutes(block.end_time, block.lineno)

        # Start and End minutes
        self.emit('=', start_min, result=f"START_MINUTES_{block.name}")
        self.emit('=', end_min, result=f"END_MINUTES_{block.name}")
        self.emit('=', block.slot_hours, result=f"SLOT_HOURS_{block.name}")

        # Duration in minutes: t1 = end - start
        t_dur_min = self.new_temp()
        self.emit('-', f"END_MINUTES_{block.name}", f"START_MINUTES_{block.name}", result=t_dur_min)

        # Duration in hours: t2 = t1 / 60
        t_dur_hours = self.new_temp()
        self.emit('/', t_dur_min, 60, result=t_dur_hours)

        # Number of slots: t3 = t2 / slot_hours
        t_num_slots = self.new_temp()
        self.emit('/', t_dur_hours, f"SLOT_HOURS_{block.name}", result=t_num_slots)

        # Rotation setup
        rot_len = len(block.rotation)
        self.emit('=', rot_len, result=f"ROTATION_LEN_{block.name}")
        for idx, grp in enumerate(block.rotation):
            self.emit('=', f"'{grp}'", result=f"ROTATION_{block.name}_{idx}")

        # Slot assignment loop
        loop_start = self.new_label()
        loop_end = self.new_label()

        slot_idx = self.new_temp()
        self.emit('=', 0, result=slot_idx)

        self.emit('LABEL', result=loop_start)
        # Condition: IF slot_idx >= t_num_slots GOTO loop_end
        cond_temp = self.new_temp()
        self.emit('>=', slot_idx, t_num_slots, result=cond_temp)
        self.emit('IF', arg1=f"{cond_temp} == 1", result=loop_end)

        # Calculate rotation index: rot_idx = slot_idx % rot_len
        # In TAC: t_rot_idx = slot_idx % rot_len
        # For each rotation group, assign slot
        # To keep TAC authentic and clean, we assign slot dynamically:
        t_group = self.new_temp()
        self.emit('=', f"ROTATION_{block.name}[{slot_idx} % {rot_len}]", result=t_group)
        self.emit('ASSIGN_SLOT', arg1=slot_idx, arg2=t_group)

        # Increment slot_idx
        t_inc = self.new_temp()
        self.emit('+', slot_idx, 1, result=t_inc)
        self.emit('=', t_inc, result=slot_idx)
        self.emit('GOTO', result=loop_start)

        self.emit('LABEL', result=loop_end)

        # Feeder hour calculations and max-hours check
        self.emit('COMMENT', comment=f"Feeder Shedding Calculation for {block.name}")
        for f_name, f in feeders.items():
            if f_name in exemptions:
                self.emit('=', 0, result=f"HOURS_{block.name}_{f_name}")
                self.emit('APPLY_EXEMPT', arg1=f_name)
            else:
                self.emit('CALC_FEEDER_HOURS', arg1=f_name, arg2=f.group, result=f"HOURS_{block.name}_{f_name}")

            # Check max hours
            self.emit('CHECK_MAX_HOURS', arg1=f_name, arg2=f.max_hours)

    def format_code(self):
        """Format TAC for display under === TAC ===."""
        lines = []
        for instr in self.instructions:
            if instr.op == 'LABEL':
                lines.append(f"{instr.result}:")
            elif instr.op == 'COMMENT':
                lines.append(f"; {instr.comment}")
            else:
                lines.append(f"    {str(instr)}")
        return "\n".join(lines)
