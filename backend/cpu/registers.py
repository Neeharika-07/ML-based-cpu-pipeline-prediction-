"""
PipelineAI - CPU Architectural Registers
Defines:
  - BranchHistoryRegister (16-bit shift register)
  - ProgramCounter (64-bit with 12-bit modulo hash)
  - RegisterFile (R0 through R15 general-purpose registers)
"""

from typing import List, Union


class BranchHistoryRegister:
    """16-bit Global Branch History Register (BHR)."""
    def __init__(self, length: int = 16):
        self.length = length
        self.bits: List[int] = [0] * length

    def shift_in(self, actual_outcome: int):
        """Shifts outcome (1=Taken, 0=Not Taken) into the most recent position (h1)."""
        self.bits = [int(actual_outcome)] + self.bits[:-1]

    def reset(self):
        self.bits = [0] * self.length

    def to_list(self) -> List[int]:
        return list(self.bits)

    def to_str(self) -> str:
        return "".join(map(str, self.bits))


class ProgramCounter:
    """64-bit Program Counter with ASLR-invariant modulo hashing."""
    def __init__(self, pc_mod: int = 4096):
        self.pc_mod = pc_mod
        self.pc: int = 0

    def set(self, address: Union[int, str]):
        if isinstance(address, str):
            self.pc = int(address, 16) if address.startswith("0x") or address.startswith("0X") else int(address)
        else:
            self.pc = int(address)

    @property
    def hashed_index(self) -> int:
        return self.pc % self.pc_mod

    @property
    def hex(self) -> str:
        return hex(self.pc)
