"""
PipelineAI - Machine Learning Preprocessing Module
Converts raw CPU branch trace logs into ML-ready training, validation, and test datasets,
and provides live feature extraction for inference in the CPU pipeline simulator.
"""

import os
import argparse
from typing import Dict, List, Tuple, Union, Optional
import numpy as np
import pandas as pd

DEFAULT_HIST_LEN = 16
DEFAULT_PC_MOD = 4096
DEFAULT_N_TRAIN = 14000
DEFAULT_N_VAL = 3000

FEATURE_COLS = ["pc_idx"] + [f"h{k}" for k in range(1, DEFAULT_HIST_LEN + 1)]
METADATA_COLS = ["trace_num", "branch_index", "split"]


class BranchPreprocessor:
    """
    Preprocessor for branch prediction traces in CPU pipelines.
    Computes hashed PC indices (pc % 4096) and 16-bit Global Branch History (h1..h16).
    """

    def __init__(self, hist_len: int = DEFAULT_HIST_LEN, pc_mod: int = DEFAULT_PC_MOD):
        self.hist_len = hist_len
        self.pc_mod = pc_mod
        self.feature_cols = ["pc_idx"] + [f"h{k}" for k in range(1, hist_len + 1)]

    def process_trace_dataframe(
        self,
        raw_df: pd.DataFrame,
        n_train: int = DEFAULT_N_TRAIN,
        n_val: int = DEFAULT_N_VAL
    ) -> pd.DataFrame:
        """
        Converts raw trace table (trace_num, branch_index, pc, taken)
        into processed features (trace_num, branch_index, split, pc_idx, h1..h16, label).
        """
        required_cols = {"trace_num", "branch_index", "pc", "taken"}
        if not required_cols.issubset(raw_df.columns):
            missing = required_cols - set(raw_df.columns)
            raise ValueError(f"Raw DataFrame missing required columns: {missing}")

        traces_out = []
        for trace_id, group in raw_df.groupby("trace_num"):
            g = group.sort_values("branch_index").reset_index(drop=True).copy()
            # Construct shift history h1..h16
            for k in range(1, self.hist_len + 1):
                g[f"h{k}"] = g["taken"].shift(k)

            # Drop warmup branches where history is incomplete
            g = g.iloc[self.hist_len:].reset_index(drop=True)

            # Modulo hash the Program Counter (ASLR invariant)
            g["pc_idx"] = g["pc"].astype("int64") % self.pc_mod
            g["label"] = g["taken"].astype(int)

            # Chronological split within trace
            pos = g.index
            g["split"] = (pos >= n_train).astype(int) + (pos >= n_train + n_val).astype(int)
            traces_out.append(g)

        if not traces_out:
            return pd.DataFrame(columns=METADATA_COLS + self.feature_cols + ["label"])

        processed = pd.concat(traces_out, ignore_index=True)
        final_cols = METADATA_COLS + self.feature_cols + ["label"]
        processed = processed[final_cols]

        for k in range(1, self.hist_len + 1):
            processed[f"h{k}"] = processed[f"h{k}"].astype(int)

        return processed

    def process_file(
        self,
        input_csv_path: str,
        output_csv_path: Optional[str] = None,
        n_train: int = DEFAULT_N_TRAIN,
        n_val: int = DEFAULT_N_VAL
    ) -> pd.DataFrame:
        """Processes raw CSV file on disk and optionally saves the output."""
        if not os.path.exists(input_csv_path):
            raise FileNotFoundError(f"Input file not found: {input_csv_path}")

        raw = pd.read_csv(input_csv_path)
        processed = self.process_trace_dataframe(raw, n_train=n_train, n_val=n_val)

        if output_csv_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)
            processed.to_csv(output_csv_path, index=False)
            print(f"[Preprocessor] Saved {len(processed):,} rows to {output_csv_path}")

        return processed

    def encode_live_branch(
        self,
        pc: Union[int, str],
        history: Union[List[int], str, int]
    ) -> pd.DataFrame:
        """
        Encodes a single live branch instruction for real-time inference in CPU simulator.
        
        Args:
            pc: Program Counter as int or hex string (e.g., 0x401020 or 4198432)
            history: 16-bit history as list of ints [h1, ..., h16], binary string "1010...", or integer bitmask
        
        Returns:
            DataFrame with columns matching FEATURE_COLS
        """
        if isinstance(pc, str):
            pc_val = int(pc, 16) if pc.startswith("0x") or pc.startswith("0X") else int(pc)
        else:
            pc_val = int(pc)

        pc_idx = pc_val % self.pc_mod

        # Parse history
        hist_vector = []
        if isinstance(history, str):
            clean_str = history.replace(" ", "").replace("_", "")
            # Ensure 16 bits
            bits = [int(b) for b in clean_str]
            if len(bits) < self.hist_len:
                bits = [0] * (self.hist_len - len(bits)) + bits
            hist_vector = bits[:self.hist_len]
        elif isinstance(history, int):
            # Bitmask: least significant bit is h1 or vice versa
            hist_vector = [(history >> (self.hist_len - 1 - i)) & 1 for i in range(self.hist_len)]
        elif isinstance(history, (list, tuple, np.ndarray)):
            hist_list = list(history)
            if len(hist_list) < self.hist_len:
                hist_list = [0] * (self.hist_len - len(hist_list)) + hist_list
            hist_vector = [int(x) for x in hist_list[:self.hist_len]]
        else:
            hist_vector = [0] * self.hist_len

        row_dict = {"pc_idx": [pc_idx]}
        for i, val in enumerate(hist_vector, start=1):
            row_dict[f"h{i}"] = [val]

        return pd.DataFrame(row_dict)[self.feature_cols]

    @staticmethod
    def load_splits(
        processed_csv_path: str
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """
        Loads preprocessed dataset and splits into Train (split=0), Val (split=1), Test (split=2).
        Features: pc_idx, h1..h16
        Target: label
        """
        if not os.path.exists(processed_csv_path):
            raise FileNotFoundError(f"Processed dataset not found: {processed_csv_path}")

        df = pd.read_csv(processed_csv_path)
        feature_cols = ["pc_idx"] + [f"h{k}" for k in range(1, DEFAULT_HIST_LEN + 1)]

        train_mask = df["split"] == 0
        val_mask = df["split"] == 1
        test_mask = df["split"] == 2

        X_train = df.loc[train_mask, feature_cols]
        y_train = df.loc[train_mask, "label"]

        X_val = df.loc[val_mask, feature_cols]
        y_val = df.loc[val_mask, "label"]

        X_test = df.loc[test_mask, feature_cols]
        y_test = df.loc[test_mask, "label"]

        return X_train, y_train, X_val, y_val, X_test, y_test


def main():
    parser = argparse.ArgumentParser(description="PipelineAI Branch Trace Preprocessor")
    parser.add_argument("--input", default="dataset/raw_dataset.csv", help="Path to raw dataset CSV")
    parser.add_argument("--output", default="dataset/processed_dataset.csv", help="Path to output processed CSV")
    parser.add_argument("--hist-len", type=int, default=DEFAULT_HIST_LEN, help="History register length")
    parser.add_argument("--pc-mod", type=int, default=DEFAULT_PC_MOD, help="Modulo for PC index hash")
    args = parser.parse_args()

    preprocessor = BranchPreprocessor(hist_len=args.hist_len, pc_mod=args.pc_mod)
    preprocessor.process_file(args.input, args.output)


if __name__ == "__main__":
    main()
