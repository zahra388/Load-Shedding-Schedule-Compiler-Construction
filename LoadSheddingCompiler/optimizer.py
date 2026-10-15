"""
TAC Optimizer for LoadSheddingLang.
JUW Compiler Construction Lab Project.

Implements two core compiler optimization passes:
1. Constant Folding & Constant Propagation
   - Replaces expressions involving known compile-time constants with their evaluated values.
   - Example: 960 - 480 -> 480, 480 / 60 -> 8, 8 / 2 -> 4 slots.
2. Dead Code Elimination (DCE)
   - Removes unreachable code after unconditional jumps.
   - Removes unused temporary variable definitions that have no downstream reads.
   - Removes unreferenced jump labels.

Roman Urdu Explanation for Viva:
Optimization phase code ko execute hone se pehle behtar (tez aur chhota) banata hai.
Constant Folding mein compile-time pe maloom values ka hisaab (calculation) pehle hi
kar liya jata hai (jaise 480/60 = 8). Dead Code Elimination mein bekar ya unused instructions
aur unreachable labels ko khatam kiya jata hai.
"""

from tac_generator import TACInstruction

class TACOptimizer:
    def __init__(self):
        self.folded_count = 0
        self.eliminated_count = 0

    def optimize(self, instructions):
        """
        Runs optimization pipeline:
        Pass 1: Constant Propagation & Folding
        Pass 2: Dead Code Elimination
        Returns: list of optimized TACInstruction
        """
        self.folded_count = 0
        self.eliminated_count = 0

        # Pass 1: Constant Folding & Propagation
        opt_pass1 = self._constant_folding(instructions)

        # Pass 2: Dead Code Elimination
        opt_pass2 = self._dead_code_elimination(opt_pass1)

        return opt_pass2

    def _constant_folding(self, instructions):
        import collections
        # Count assignments to each variable
        assign_counts = collections.Counter()
        for instr in instructions:
            if instr.op in ('=', '+', '-', '*', '/', '>=', '<=', '==', '>', '<') and instr.result:
                assign_counts[instr.result] += 1

        # Only variables assigned exactly once can be compile-time propagated
        single_assign_vars = {k for k, count in assign_counts.items() if count == 1}

        constants = {}
        new_instrs = []

        for instr in instructions:
            if instr.op in ('COMMENT', 'LABEL'):
                new_instrs.append(instr)
                continue

            # Resolve arg1 and arg2 from known constants ONLY if they are single-assigned
            arg1_val = constants.get(instr.arg1, instr.arg1) if instr.arg1 in single_assign_vars else instr.arg1
            arg2_val = constants.get(instr.arg2, instr.arg2) if instr.arg2 in single_assign_vars else instr.arg2

            # Check if assignment of literal constant to a single-assign variable
            if instr.op == '=' and instr.result in single_assign_vars:
                if isinstance(arg1_val, (int, float)):
                    constants[instr.result] = arg1_val
                    new_instrs.append(TACInstruction('=', arg1_val, None, instr.result, instr.comment))
                    continue
                elif isinstance(arg1_val, str) and (arg1_val.isdigit() or (arg1_val.startswith('-') and arg1_val[1:].isdigit())):
                    constants[instr.result] = int(arg1_val)
                    new_instrs.append(TACInstruction('=', int(arg1_val), None, instr.result, instr.comment))
                    continue

            # Check binary arithmetic folding for single-assign variables
            if instr.op in ('+', '-', '*', '/') and instr.result in single_assign_vars:
                val1 = self._try_number(arg1_val)
                val2 = self._try_number(arg2_val)

                if val1 is not None and val2 is not None:
                    # Evaluate arithmetic at compile time!
                    res_val = None
                    if instr.op == '+':
                        res_val = val1 + val2
                    elif instr.op == '-':
                        res_val = val1 - val2
                    elif instr.op == '*':
                        res_val = val1 * val2
                    elif instr.op == '/' and val2 != 0:
                        res_val = val1 / val2
                        if res_val.is_integer():
                            res_val = int(res_val)

                    if res_val is not None:
                        constants[instr.result] = res_val
                        self.folded_count += 1
                        new_instrs.append(TACInstruction('=', res_val, None, instr.result, f"Folded: {val1} {instr.op} {val2}"))
                        continue

            # Default: update instruction with propagated values for single-assign operands
            new_instrs.append(TACInstruction(instr.op, arg1_val, arg2_val, instr.result, instr.comment))

        return new_instrs

    def _dead_code_elimination(self, instructions):
        # 1. Identify all referenced labels and variables
        used_labels = set()
        used_vars = set()

        for instr in instructions:
            if instr.op == 'GOTO':
                used_labels.add(instr.result)
            elif instr.op == 'IF':
                used_labels.add(instr.result)
                # Check variable references in IF condition
                if instr.arg1:
                    for token in str(instr.arg1).split():
                        used_vars.add(token)
            elif instr.op in ('+', '-', '*', '/', '==', '<=', '>=', '<', '>'):
                if instr.arg1: used_vars.add(str(instr.arg1))
                if instr.arg2: used_vars.add(str(instr.arg2))
            elif instr.op in ('ASSIGN_SLOT', 'CALC_FEEDER_HOURS', 'APPLY_EXEMPT', 'CHECK_MAX_HOURS'):
                if instr.arg1: used_vars.add(str(instr.arg1))
                if instr.arg2: used_vars.add(str(instr.arg2))
            elif instr.op == '=':
                if instr.arg1: used_vars.add(str(instr.arg1))

        # 2. Filter instructions: remove unreferenced temporary variables and unreachable code
        result = []
        unreachable = False

        for instr in instructions:
            if instr.op == 'LABEL':
                unreachable = False
                # If label is never targeted and is purely an internal label, it can be pruned if desired
                # But we keep loop labels for structural readability unless completely dead
                result.append(instr)
                continue

            if unreachable and instr.op != 'LABEL':
                self.eliminated_count += 1
                continue

            # Remove assignment to a temporary variable if that temp is NEVER read anywhere
            # (e.g. intermediate temps that were folded away)
            if instr.op == '=' and instr.result and instr.result.startswith('t'):
                if instr.result not in used_vars:
                    # Dead temporary assignment
                    self.eliminated_count += 1
                    continue

            result.append(instr)

            # If unconditional GOTO, following instructions until next LABEL are unreachable
            if instr.op == 'GOTO':
                unreachable = True

        return result

    def _try_number(self, val):
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str):
            try:
                if '.' in val:
                    return float(val)
                return int(val)
            except ValueError:
                return None
        return None

def format_optimized_tac(instructions):
    """Format optimized TAC under === OPTIMIZED TAC ===."""
    lines = []
    for instr in instructions:
        if instr.op == 'LABEL':
            lines.append(f"{instr.result}:")
        elif instr.op == 'COMMENT':
            lines.append(f"; {instr.comment}")
        else:
            lines.append(f"    {str(instr)}")
    return "\n".join(lines)
