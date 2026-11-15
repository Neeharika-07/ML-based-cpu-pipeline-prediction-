"""
PipelineAI - CPU Stages Definition
Defines individual microarchitectural stages for a 5-stage RISC processor:
  - IF  (Instruction Fetch)
  - ID  (Instruction Decode)
  - EX  (Execute / ALU & Branch Evaluation)
  - MEM (Data Memory Access)
  - WB  (Register Writeback / Instruction Commit)
"""

from typing import Dict, Any, Optional


class CPUPipelineStage:
    """Represents a single hardware stage in the 5-stage CPU pipeline."""
    def __init__(self, name: str):
        self.name = name
        self.current_instruction: Optional[Dict[str, Any]] = None
        self.is_bubble: bool = True
        self.is_stalled: bool = False

    def clear(self):
        """Clears stage contents, inserting a NOP bubble."""
        self.current_instruction = None
        self.is_bubble = True
        self.is_stalled = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.name,
            "instruction": self.current_instruction,
            "is_bubble": self.is_bubble,
            "is_stalled": self.is_stalled
        }
