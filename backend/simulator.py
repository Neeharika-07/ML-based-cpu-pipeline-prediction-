"""
PipelineAI - Cycle-Accurate CPU Pipeline Simulator Engine
Simulates a classic 5-Stage RISC Pipeline (IF, ID, EX, MEM, WB) with
speculative execution, branch prediction, hazard detection, and pipeline flushes.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import joblib

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.preprocessing import BranchPreprocessor, DEFAULT_HIST_LEN, DEFAULT_PC_MOD
from ml.baseline_models import (
    TwoBitSaturatingCounterPredictor,
    GsharePredictor,
    PerceptronPredictor
)


class CPUPipelineStage:
    """Represents a single stage in the CPU pipeline."""
    def __init__(self, name: str):
        self.name = name
        self.current_instruction: Optional[Dict[str, Any]] = None
        self.is_bubble: bool = True
        self.is_stalled: bool = False

    def clear(self):
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


class CPUPipelineSimulator:
    """
    Cycle-accurate 5-Stage CPU Pipeline Simulator with Branch Prediction.
    
    Stages:
      1. IF  (Instruction Fetch): Fetches instruction, invokes Branch Predictor
      2. ID  (Instruction Decode): Decodes operands and registers
      3. EX  (Execute): Resolves branch outcome; triggers flush if mispredicted!
      4. MEM (Memory Access): Memory read/write operations
      5. WB  (Write Back): Commits instruction retirement to register file
    """

    def __init__(
        self,
        misprediction_penalty: int = 2,
        model_dir: Optional[str] = None
    ):
        self.misprediction_penalty = misprediction_penalty
        if model_dir is None:
            self.model_dir = os.path.join(PROJECT_ROOT, "ml", "model")
        else:
            self.model_dir = model_dir

        self.preprocessor = BranchPreprocessor()

        # Load models
        self.xgb_model = None
        self.baselines = {}
        self._load_models()

        # Pipeline stages
        self.stages = {
            "IF": CPUPipelineStage("IF"),
            "ID": CPUPipelineStage("ID"),
            "EX": CPUPipelineStage("EX"),
            "MEM": CPUPipelineStage("MEM"),
            "WB": CPUPipelineStage("WB")
        }

        # Simulation metrics
        self.clock_cycle: int = 0
        self.instructions_retired: int = 0
        self.branches_encountered: int = 0
        self.branches_predicted_correctly: int = 0
        self.branches_mispredicted: int = 0
        self.total_stall_cycles: int = 0
        self.flushes_occurred: int = 0

        # Architectural registers
        self.pc: int = 0
        self.bhr: List[int] = [0] * DEFAULT_HIST_LEN  # 16-bit Global Branch History Register
        self.history_log: List[Dict[str, Any]] = []

    def _load_models(self):
        xgb_file = os.path.join(self.model_dir, "branch_predictor_xgb.joblib")
        if os.path.exists(xgb_file):
            try:
                self.xgb_model = joblib.load(xgb_file)
            except Exception as e:
                print(f"[Simulator] Warning: Could not load XGBoost model: {e}")

        baselines_file = os.path.join(self.model_dir, "baseline_predictors.joblib")
        if os.path.exists(baselines_file):
            try:
                self.baselines = joblib.load(baselines_file)
            except Exception as e:
                print(f"[Simulator] Warning: Could not load baseline models: {e}")

    def reset(self):
        """Resets the simulator state."""
        for stage in self.stages.values():
            stage.clear()

        self.clock_cycle = 0
        self.instructions_retired = 0
        self.branches_encountered = 0
        self.branches_predicted_correctly = 0
        self.branches_mispredicted = 0
        self.total_stall_cycles = 0
        self.flushes_occurred = 0
        self.pc = 0
        self.bhr = [0] * DEFAULT_HIST_LEN
        self.history_log.clear()

    def predict_branch(self, pc: int, predictor_type: str = "xgboost") -> Tuple[int, float]:
        """
        Queries selected branch predictor for a given PC and current BHR state.
        Returns: (predicted_taken [0 or 1], confidence/probability)
        """
        p_type = predictor_type.lower()

        if p_type == "static_not_taken":
            return 0, 1.0
        elif p_type == "static_taken":
            return 1, 1.0

        feat_df = self.preprocessor.encode_live_branch(pc, self.bhr)

        if p_type == "xgboost" and self.xgb_model is not None:
            pred = int(self.xgb_model.predict(feat_df)[0])
            proba = float(self.xgb_model.predict_proba(feat_df)[0][pred])
            return pred, proba

        if p_type == "perceptron" and "perceptron" in self.baselines:
            model = self.baselines["perceptron"]
            pred = int(model.predict(feat_df)[0])
            proba = float(model.predict_proba(feat_df)[0][pred])
            return pred, proba

        if p_type == "gshare" and "gshare" in self.baselines:
            model = self.baselines["gshare"]
            pred = int(model.predict(feat_df)[0])
            proba = float(model.predict_proba(feat_df)[0][pred])
            return pred, proba

        if p_type == "bimodal" and "bimodal" in self.baselines:
            model = self.baselines["bimodal"]
            pred = int(model.predict(feat_df)[0])
            proba = float(model.predict_proba(feat_df)[0][pred])
            return pred, proba

        return 1 if (pc % 2 == 1) else 0, 0.5

    def update_bhr(self, actual_outcome: int):
        """Updates the 16-bit shift register with the actual branch outcome."""
        self.bhr = [int(actual_outcome)] + self.bhr[:-1]

    def run_trace(
        self,
        branch_records: List[Dict[str, Any]],
        predictor_type: str = "xgboost",
        max_cycles: int = 10000,
        record_cycles: bool = True
    ) -> Dict[str, Any]:
        """
        Executes an entire sequence of branch instructions through the pipeline.
        Calculates execution cycles, stall bubbles, flush penalties, and IPC/CPI.
        """
        self.reset()
        idx = 0
        total_branches = len(branch_records)
        active_pipeline = True
        cycle_traces = []

        flush_stalls_remaining = 0

        while (idx < total_branches or active_pipeline) and (self.clock_cycle < max_cycles):
            self.clock_cycle += 1
            flush_this_cycle = False
            misprediction_occurred = False

            # Stage 5: WB (Write Back)
            wb_instr = self.stages["WB"].current_instruction
            if wb_instr and not self.stages["WB"].is_bubble:
                self.instructions_retired += 1

            # Stage 4: MEM (Memory) -> WB
            self.stages["WB"].current_instruction = self.stages["MEM"].current_instruction
            self.stages["WB"].is_bubble = self.stages["MEM"].is_bubble

            # Stage 3: EX (Execute) -> MEM
            ex_instr = self.stages["EX"].current_instruction
            self.stages["MEM"].current_instruction = ex_instr
            self.stages["MEM"].is_bubble = self.stages["EX"].is_bubble

            # Branch Resolution happens in EX stage!
            if ex_instr and not self.stages["EX"].is_bubble and ex_instr.get("is_branch"):
                actual = ex_instr["actual_taken"]
                predicted = ex_instr["predicted_taken"]

                self.branches_encountered += 1
                if predicted == actual:
                    self.branches_predicted_correctly += 1
                else:
                    self.branches_mispredicted += 1
                    self.flushes_occurred += 1
                    flush_this_cycle = True
                    misprediction_occurred = True
                    flush_stalls_remaining = self.misprediction_penalty
                    self.total_stall_cycles += self.misprediction_penalty

                self.update_bhr(actual)

            # Stage 2: ID (Decode) -> EX
            if flush_this_cycle:
                self.stages["EX"].clear()
                self.stages["ID"].clear()
            else:
                self.stages["EX"].current_instruction = self.stages["ID"].current_instruction
                self.stages["EX"].is_bubble = self.stages["ID"].is_bubble

            # Stage 1: IF (Fetch) -> ID
            if flush_this_cycle:
                self.stages["IF"].clear()
            elif flush_stalls_remaining > 0:
                self.stages["ID"].clear()
                flush_stalls_remaining -= 1
            else:
                self.stages["ID"].current_instruction = self.stages["IF"].current_instruction
                self.stages["ID"].is_bubble = self.stages["IF"].is_bubble

                # Fetch next instruction into IF
                if idx < total_branches:
                    item = branch_records[idx]
                    raw_pc = item.get("pc", 0)
                    if pd.isna(raw_pc):
                        raw_pc = 0
                    pc = int(float(raw_pc))

                    raw_taken = item.get("taken", item.get("label", 0))
                    if pd.isna(raw_taken):
                        raw_taken = 0
                    actual_taken = int(float(raw_taken))

                    pred_taken, proba = self.predict_branch(pc, predictor_type)

                    instr_packet = {
                        "id": idx + 1,
                        "pc": pc,
                        "pc_hex": hex(pc),
                        "pc_idx": pc % DEFAULT_PC_MOD,
                        "is_branch": True,
                        "predicted_taken": pred_taken,
                        "actual_taken": actual_taken,
                        "confidence": round(proba, 4),
                        "opcode": "BEQ" if pred_taken else "BNE"
                    }
                    self.stages["IF"].current_instruction = instr_packet
                    self.stages["IF"].is_bubble = False
                    idx += 1
                else:
                    self.stages["IF"].clear()

            active_pipeline = any(not s.is_bubble for s in self.stages.values())

            if record_cycles and (len(cycle_traces) < 250):
                cycle_traces.append({
                    "cycle": self.clock_cycle,
                    "stages": {k: v.to_dict() for k, v in self.stages.items()},
                    "bhr": "".join(map(str, self.bhr)),
                    "bhr_list": list(self.bhr),
                    "misprediction": misprediction_occurred,
                    "retired_so_far": self.instructions_retired
                })

        accuracy = (
            (self.branches_predicted_correctly / self.branches_encountered)
            if self.branches_encountered > 0 else 1.0
        )
        mispred_rate = 1.0 - accuracy
        cpi = (self.clock_cycle / self.instructions_retired) if self.instructions_retired > 0 else 1.0
        ipc = (self.instructions_retired / self.clock_cycle) if self.clock_cycle > 0 else 1.0
        mpki = (self.branches_mispredicted / max(1, self.instructions_retired)) * 1000.0

        return {
            "predictor": predictor_type,
            "total_cycles": self.clock_cycle,
            "instructions_retired": self.instructions_retired,
            "branches_encountered": self.branches_encountered,
            "branches_predicted_correctly": self.branches_predicted_correctly,
            "branches_mispredicted": self.branches_mispredicted,
            "accuracy": round(accuracy, 4),
            "misprediction_rate": round(mispred_rate, 4),
            "total_stall_cycles": self.total_stall_cycles,
            "flushes_occurred": self.flushes_occurred,
            "cpi": round(cpi, 4),
            "ipc": round(ipc, 4),
            "mpki": round(mpki, 2),
            "cycle_traces": cycle_traces
        }

    def compare_all_predictors(
        self,
        branch_records: List[Dict[str, Any]],
        max_samples: int = 500
    ) -> Dict[str, Any]:
        """
        Runs the trace through all predictor architectures to generate a side-by-side benchmark.
        """
        sample_records = branch_records[:max_samples]
        predictors = ["static_not_taken", "static_taken", "bimodal", "gshare", "perceptron", "xgboost"]
        results = {}

        for p in predictors:
            res = self.run_trace(sample_records, predictor_type=p, record_cycles=False)
            results[p] = {
                "predictor": p,
                "total_cycles": res["total_cycles"],
                "stalls": res["total_stall_cycles"],
                "mispredictions": res["branches_mispredicted"],
                "accuracy": res["accuracy"],
                "cpi": res["cpi"],
                "ipc": res["ipc"],
                "mpki": res["mpki"]
            }

        baseline_cycles = results["static_not_taken"]["total_cycles"]
        for p, data in results.items():
            speedup = baseline_cycles / data["total_cycles"] if data["total_cycles"] > 0 else 1.0
            data["speedup_vs_baseline"] = round(speedup, 3)

        return results
