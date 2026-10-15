"""
Semantic Analyzer for LoadSheddingLang.
JUW Compiler Construction Lab Project.

Enforces all mandatory rules R1–R7:
- R1: Unique feeder and group assignment
- R2: Exempt feeders (hours must always be 0; feeder must exist)
- R3 & R6: Maximum shedding hours check with detailed error message
- R4: Exact division of block duration into slot length
- R5: Valid group rotation (all rotation groups must have feeders, all feeder groups must appear)
- R7: Valid 24-hour clock and positive duration values

Roman Urdu Explanation for Viva:
Semantic Analysis compiler ka teesra ahem marhala hai jo program ke "meaning" aur "logic"
ko verify karta hai. Yeh check karta hai ke rules R1 se R7 tak sab follow ho rahe hain:
jaise koi duplicate feeder na ho, time valid ho (00:00 se 23:59), slots duration pe
poori divide hoti hon, aur kisi feeder ke shedding hours uske maximum limit se exceed na hon.
"""

from ast_nodes import FeederNode, ExemptNode, ScheduleBlockNode

def parse_time_to_minutes(time_str, lineno, context=""):
    """
    Parses 'HH:MM' 24-hour time to minutes from midnight.
    Validates R7 (HH: 00-23, MM: 00-59).
    Returns (minutes, error_or_None)
    """
    parts = time_str.split(':')
    if len(parts) != 2:
        return None, f"Semantic error (line {lineno}): invalid time format '{time_str}' in {context}. Must be 24-hour clock 'HH:MM'."
    try:
        h = int(parts[0])
        m = int(parts[1])
    except ValueError:
        return None, f"Semantic error (line {lineno}): non-numeric time '{time_str}' in {context}."

    if not (0 <= h <= 23):
        return None, f"Semantic error (line {lineno}): invalid hour '{h:02d}' in time '{time_str}'. Hours must be between 00 and 23."
    if not (0 <= m <= 59):
        return None, f"Semantic error (line {lineno}): invalid minute '{m:02d}' in time '{time_str}'. Minutes must be between 00 and 59."

    return h * 60 + m, None


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.feeders = {}       # name -> FeederNode
        self.exemptions = set() # set of feeder names
        self.groups = {}        # group_name -> list of feeder names
        self.blocks = []        # list of ScheduleBlockNode

    def analyze(self, ast_root):
        """
        Runs comprehensive semantic analysis over AST.
        Returns: (success: bool, errors: list, warnings: list)
        """
        self.errors = []
        self.warnings = []
        self.feeders = {}
        self.exemptions = set()
        self.groups = {}
        self.blocks = []

        if not ast_root or not hasattr(ast_root, 'statements'):
            self.errors.append("Semantic error (line 1): empty AST or invalid program structure.")
            return False, self.errors, self.warnings

        # Phase 1: Collect declarations & check R1, R7
        for stmt in ast_root.statements:
            if isinstance(stmt, FeederNode):
                self._check_feeder(stmt)
            elif isinstance(stmt, ExemptNode):
                self._check_exempt(stmt)
            elif isinstance(stmt, ScheduleBlockNode):
                self.blocks.append(stmt)

        # Phase 2: Check R2 (exempt feeders must be defined)
        for ex_name in self.exemptions:
            if ex_name not in self.feeders:
                # Find line number from AST
                ex_line = 1
                for s in ast_root.statements:
                    if isinstance(s, ExemptNode) and s.feeder_name == ex_name:
                        ex_line = s.lineno
                        break
                self.errors.append(
                    f"Semantic error (line {ex_line}): exempt feeder '{ex_name}' is not defined. Declare the feeder before exempting it."
                )

        # Phase 3: Check Schedule Blocks against R3, R4, R5, R6, R7
        if not self.blocks:
            self.warnings.append("Warning (line 1): no schedule blocks defined in program.")

        for block in self.blocks:
            self._check_block(block)

        success = len(self.errors) == 0
        return success, self.errors, self.warnings

    def _check_feeder(self, stmt):
        # R1: Unique feeder assignment
        if stmt.name in self.feeders:
            prev = self.feeders[stmt.name]
            self.errors.append(
                f"Semantic error (line {stmt.lineno}): duplicate feeder '{stmt.name}' already declared at line {prev.lineno}. Feeder names must be unique (Rule R1)."
            )
            return

        # R7: Valid numbers
        if stmt.max_hours < 0:
            self.errors.append(
                f"Semantic error (line {stmt.lineno}): maximum shedding hours for feeder '{stmt.name}' must be non-negative (found {stmt.max_hours})."
            )

        if not (0 <= stmt.loss <= 100):
            self.errors.append(
                f"Semantic error (line {stmt.lineno}): line loss percentage for feeder '{stmt.name}' must be between 0% and 100% (found {stmt.loss}%)."
            )

        self.feeders[stmt.name] = stmt
        if stmt.group not in self.groups:
            self.groups[stmt.group] = []
        self.groups[stmt.group].append(stmt.name)

    def _check_exempt(self, stmt):
        self.exemptions.add(stmt.feeder_name)

    def _check_block(self, block):
        # R7: Parse and validate start & end times
        start_min, err_start = parse_time_to_minutes(block.start_time, block.lineno, f"block '{block.name}'")
        if err_start:
            self.errors.append(err_start)
            return

        end_min, err_end = parse_time_to_minutes(block.end_time, block.lineno, f"block '{block.name}'")
        if err_end:
            self.errors.append(err_end)
            return

        if end_min <= start_min:
            self.errors.append(
                f"Semantic error (line {block.lineno}): end time ({block.end_time}) must be after start time ({block.start_time}) in block '{block.name}'."
            )
            return

        duration_min = end_min - start_min
        duration_hours = duration_min / 60.0

        # R7: Slot duration
        if block.slot_hours <= 0:
            self.errors.append(
                f"Semantic error (line {block.lineno}): slot length in block '{block.name}' must be positive (found {block.slot_hours} hours)."
            )
            return

        slot_min = int(block.slot_hours * 60)

        # R4: Exact division into slots
        if duration_min % slot_min != 0:
            self.errors.append(
                f"Semantic error (line {block.lineno}): block '{block.name}' duration ({duration_hours:g} hours from {block.start_time} to {block.end_time}) does not divide exactly into slot length of {block.slot_hours} hours (Rule R4). Adjust duration or slot size."
            )
            return

        num_slots = duration_min // slot_min

        # R5: Valid group rotation
        if not block.rotation:
            self.errors.append(
                f"Semantic error (line {block.lineno}): rotation for block '{block.name}' is empty. Must specify at least one group."
            )
            return

        # Check every group named in rotation contains at least one feeder
        for grp in block.rotation:
            if grp not in self.groups or len(self.groups[grp]) == 0:
                self.errors.append(
                    f"Semantic error (line {block.lineno}): group '{grp}' in rotation of block '{block.name}' contains no declared feeders (Rule R5). Define feeders for group '{grp}' or remove it from rotation."
                )

        # Check every declared feeder's group appears in the rotation
        for grp_name, f_list in self.groups.items():
            if grp_name not in block.rotation:
                self.errors.append(
                    f"Semantic error (line {block.lineno}): group '{grp_name}' (containing feeders: {', '.join(f_list)}) is missing from rotation of block '{block.name}' (Rule R5). All feeder groups must appear in rotation."
                )

        # If there are already errors in rotation or times, stop calculation for this block
        if self.errors:
            return

        # Calculate slot allocations
        group_hours = {g: 0 for g in self.groups}
        for i in range(num_slots):
            grp = block.rotation[i % len(block.rotation)]
            group_hours[grp] += block.slot_hours

        # R3 & R6: Check maximum shedding hours per feeder
        for f_name, feeder in self.feeders.items():
            if f_name in self.exemptions:
                # R2: Exempt feeders must never be shed
                calc_hours = 0
            else:
                calc_hours = group_hours.get(feeder.group, 0)

            # R3 & R6: Feeder exceeds maximum
            if calc_hours > feeder.max_hours:
                self.errors.append(
                    f"Semantic error (line {block.lineno}): feeder {f_name} in block {block.name} receives {calc_hours} hours, exceeding its maximum of {feeder.max_hours} hours. Reduce its scheduled hours or increase its permitted maximum."
                )
