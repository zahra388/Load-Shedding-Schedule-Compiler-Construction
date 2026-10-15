"""
TAC Execution Engine (Virtual Machine / Interpreter) for LoadSheddingLang.
JUW Compiler Construction Lab Project.

Executes TAC instructions in software without using eval().
Calculates:
- Number of slots and boundaries
- Assigned group for each slot
- Timetable table (e.g. 08:00–10:00 | A)
- Group shedding totals
- Feeder shedding totals
- Exemption enforcement (0 hours for exempt)
- Max hours verification against limits

Roman Urdu Explanation for Viva:
TAC Executor compiler ka Target / Runtime Execution Engine hai.
Yeh generated Three-Address Code ko step-by-step interpret karta hai bina eval() use kiye.
Virtual registers aur memory maintain karta hai, rotation loop chalata hai,
aur final timetable aur feeder hours calculate karke display karta hai.
"""

def format_minutes_to_time(minutes):
    """Converts minutes from midnight to 'HH:MM' string."""
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

class TACExecutionEngine:
    def __init__(self):
        self.memory = {}          # variable/register storage
        self.labels = {}          # label name -> instruction index
        self.errors = []
        self.timetable = []       # list of {slot_index, start_min, end_min, group}
        self.group_hours = {}     # group_name -> total hours
        self.feeder_hours = {}    # feeder_name -> total hours
        self.exemptions = set()
        self.max_hours = {}       # feeder_name -> max permitted
        self.feeder_groups = {}   # feeder_name -> group
        self.block_info = {}

    def execute(self, instructions):
        """
        Interprets the list of TAC instructions sequentially.
        Returns: ExecutionResult object
        """
        self.memory = {}
        self.labels = {}
        self.errors = []
        self.timetable = []
        self.group_hours = {}
        self.feeder_hours = {}
        self.exemptions = set()
        self.max_hours = {}
        self.feeder_groups = {}
        self.block_info = {}

        # First pass: map label positions
        for idx, instr in enumerate(instructions):
            if instr.op == 'LABEL':
                self.labels[instr.result] = idx

        # Second pass: execute
        pc = 0
        max_steps = 100000  # safety threshold against infinite loops
        step_count = 0

        while pc < len(instructions) and step_count < max_steps:
            step_count += 1
            instr = instructions[pc]

            if instr.op in ('COMMENT', 'LABEL'):
                pc += 1
                continue

            elif instr.op == '=':
                val = self._resolve_val(instr.arg1)
                self.memory[instr.result] = val
                pc += 1

            elif instr.op in ('+', '-', '*', '/'):
                val1 = self._resolve_num(instr.arg1)
                val2 = self._resolve_num(instr.arg2)
                res = 0
                if instr.op == '+': res = val1 + val2
                elif instr.op == '-': res = val1 - val2
                elif instr.op == '*': res = val1 * val2
                elif instr.op == '/':
                    res = val1 / val2 if val2 != 0 else 0
                    if isinstance(res, float) and res.is_integer():
                        res = int(res)
                self.memory[instr.result] = res
                pc += 1

            elif instr.op in ('>=', '<=', '==', '>', '<'):
                val1 = self._resolve_num(instr.arg1)
                val2 = self._resolve_num(instr.arg2)
                cond = False
                if instr.op == '>=': cond = val1 >= val2
                elif instr.op == '<=': cond = val1 <= val2
                elif instr.op == '==': cond = val1 == val2
                elif instr.op == '>': cond = val1 > val2
                elif instr.op == '<': cond = val1 < val2
                self.memory[instr.result] = 1 if cond else 0
                pc += 1

            elif instr.op == 'GOTO':
                target = instr.result
                if target in self.labels:
                    pc = self.labels[target]
                else:
                    self.errors.append(f"Runtime error: unknown jump label '{target}'")
                    break

            elif instr.op == 'IF':
                # Format: arg1 = "cond_temp == 1", result = label
                cond_expr = str(instr.arg1)
                should_jump = False
                if '==' in cond_expr:
                    left, right = [x.strip() for x in cond_expr.split('==')]
                    v_left = self._resolve_num(left)
                    v_right = self._resolve_num(right)
                    should_jump = (v_left == v_right)
                else:
                    val = self._resolve_num(cond_expr)
                    should_jump = bool(val)

                if should_jump:
                    target = instr.result
                    if target in self.labels:
                        pc = self.labels[target]
                    else:
                        self.errors.append(f"Runtime error: unknown jump label '{target}'")
                        break
                else:
                    pc += 1

            elif instr.op == 'ASSIGN_SLOT':
                slot_idx = self._resolve_num(instr.arg1)
                grp = str(self._resolve_val(instr.arg2)).strip("'\"")
                self.timetable.append({
                    "slot_index": slot_idx,
                    "group": grp
                })
                self.group_hours[grp] = self.group_hours.get(grp, 0)
                pc += 1

            elif instr.op == 'APPLY_EXEMPT':
                feeder_name = str(self._resolve_val(instr.arg1)).strip("'\"")
                self.exemptions.add(feeder_name)
                self.feeder_hours[feeder_name] = 0
                pc += 1

            elif instr.op == 'CALC_FEEDER_HOURS':
                feeder_name = str(self._resolve_val(instr.arg1)).strip("'\"")
                group_name = str(self._resolve_val(instr.arg2)).strip("'\"")
                self.feeder_groups[feeder_name] = group_name
                # Hours from group total
                g_hrs = self.group_hours.get(group_name, 0)
                if feeder_name in self.exemptions:
                    self.feeder_hours[feeder_name] = 0
                else:
                    self.feeder_hours[feeder_name] = g_hrs
                pc += 1

            elif instr.op == 'CHECK_MAX_HOURS':
                feeder_name = str(self._resolve_val(instr.arg1)).strip("'\"")
                max_h = self._resolve_num(instr.arg2)
                self.max_hours[feeder_name] = max_h
                pc += 1

            else:
                pc += 1

        # Post-execution resolution: Calculate slot timestamps and group hours
        # Discover block name and times from memory
        block_name = "Weekday"
        start_min = 480
        end_min = 960
        slot_hours = 2

        for k, v in self.memory.items():
            if k.startswith("START_MINUTES_"):
                block_name = k.replace("START_MINUTES_", "")
                start_min = int(v)
            elif k.startswith("END_MINUTES_"):
                end_min = int(v)
            elif k.startswith("SLOT_HOURS_"):
                slot_hours = int(v)

        slot_duration_min = slot_hours * 60

        # Calculate time range for each assigned slot
        for idx, entry in enumerate(self.timetable):
            s_min = start_min + idx * slot_duration_min
            e_min = s_min + slot_duration_min
            entry["start_time"] = format_minutes_to_time(s_min)
            entry["end_time"] = format_minutes_to_time(e_min)

        # Recalculate group totals accurately from slots
        self.group_hours = {}
        for entry in self.timetable:
            g = entry["group"]
            self.group_hours[g] = self.group_hours.get(g, 0) + slot_hours

        # Recalculate feeder hours
        for f_name, g_name in self.feeder_groups.items():
            if f_name in self.exemptions:
                self.feeder_hours[f_name] = 0
            else:
                self.feeder_hours[f_name] = self.group_hours.get(g_name, 0)

        # Build validation results
        validation = {}
        for f_name, hrs in self.feeder_hours.items():
            limit = self.max_hours.get(f_name, 24)
            is_exempt = f_name in self.exemptions
            passed = hrs <= limit
            validation[f_name] = {
                "hours": hrs,
                "limit": limit,
                "is_exempt": is_exempt,
                "passed": passed
            }

        return {
            "block_name": block_name,
            "start_time": format_minutes_to_time(start_min),
            "end_time": format_minutes_to_time(end_min),
            "slot_hours": slot_hours,
            "num_slots": len(self.timetable),
            "timetable": self.timetable,
            "group_hours": self.group_hours,
            "feeder_hours": self.feeder_hours,
            "exemptions": list(self.exemptions),
            "validation": validation,
            "success": len(self.errors) == 0 and all(v["passed"] for v in validation.values())
        }

    def _resolve_val(self, operand):
        if operand is None:
            return None
        if isinstance(operand, (int, float)):
            return operand
        op_str = str(operand).strip()
        # Check if operand is array indexing like ROTATION_Weekday[0 % 2]
        if '[' in op_str and op_str.endswith(']'):
            base = op_str[:op_str.index('[')].strip()
            idx_part = op_str[op_str.index('[') + 1:-1].strip()
            # Evaluate index
            calc_idx = 0
            if '%' in idx_part:
                left, right = [x.strip() for x in idx_part.split('%')]
                v_left = self._resolve_num(left)
                v_right = self._resolve_num(right)
                calc_idx = v_left % v_right if v_right != 0 else 0
            else:
                calc_idx = self._resolve_num(idx_part)
            var_name = f"{base}_{calc_idx}"
            return self.memory.get(var_name, "A")

        if op_str in self.memory:
            return self.memory[op_str]
        # Check quoted string
        if (op_str.startswith("'") and op_str.endswith("'")) or (op_str.startswith('"') and op_str.endswith('"')):
            return op_str[1:-1]
        # Check integer
        if op_str.isdigit() or (op_str.startswith('-') and op_str[1:].isdigit()):
            return int(op_str)
        try:
            return float(op_str)
        except ValueError:
            return op_str

    def _resolve_num(self, operand):
        v = self._resolve_val(operand)
        if isinstance(v, (int, float)):
            return v
        try:
            return int(v)
        except (ValueError, TypeError):
            try:
                return float(v)
            except (ValueError, TypeError):
                return 0

def format_result(res):
    """
    Formats the execution result under === RESULT === as required by Section 12.
    """
    lines = []
    lines.append(f"Schedule Block : {res['block_name']}")
    lines.append(f"Time Range     : {res['start_time']} – {res['end_time']}")
    lines.append(f"Slot Length    : {res['slot_hours']} hours")
    lines.append(f"Total Slots    : {res['num_slots']}")
    lines.append("")
    lines.append("--- GENERATED TIMETABLE ---")
    lines.append(f"{'Time Slot':<16} | {'Assigned Group':<16}")
    lines.append("-" * 17 + "+-" + "-" * 17)
    for row in res['timetable']:
        slot_str = f"{row.get('start_time', '00:00')}–{row.get('end_time', '00:00')}"
        lines.append(f"{slot_str:<16} | {row['group']:<16}")

    lines.append("")
    lines.append("--- GROUP TOTALS ---")
    for grp, hrs in sorted(res['group_hours'].items()):
        lines.append(f"Group {grp:<6}: {hrs} hours")

    lines.append("")
    lines.append("--- FEEDER SHEDDING HOURS ---")
    for f_name, v in sorted(res['validation'].items()):
        exempt_tag = " [EXEMPT - 0 HOURS]" if v['is_exempt'] else ""
        lines.append(f"Feeder {f_name:<10}: {v['hours']} hours (Max permitted: {v['limit']}h){exempt_tag}")

    lines.append("")
    lines.append("--- VALIDATION & STATUS ---")
    all_ok = True
    for f_name, v in sorted(res['validation'].items()):
        if not v['passed']:
            all_ok = False
            lines.append(f"FAILURE: Feeder '{f_name}' scheduled for {v['hours']}h exceeds limit of {v['limit']}h.")
        else:
            lines.append(f"PASSED : Feeder '{f_name}' within limit ({v['hours']}h <= {v['limit']}h).")

    lines.append("")
    if all_ok and res['success']:
        lines.append("Compilation and scheduling succeeded successfully.")
    else:
        lines.append("Compilation stopped due to rule violations.")

    return "\n".join(lines)
