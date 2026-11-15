"""
PipelineAI - Baseline & Heuristic Microarchitectural Branch Predictor Models
Defines traditional hardware and neural predictor implementations:
  1. TwoBitSaturatingCounterPredictor (Smith Bimodal Predictor)
  2. GsharePredictor (PC XOR Global History Register)
  3. PerceptronPredictor (Jiménez & Lin Neural Branch Predictor)
"""

import numpy as np
import pandas as pd

DEFAULT_HIST_LEN = 16
DEFAULT_PC_MOD = 4096


class TwoBitSaturatingCounterPredictor:
    """Hardware 2-bit Bimodal Saturating Counter branch predictor."""
    def __init__(self, table_size: int = DEFAULT_PC_MOD):
        self.table_size = table_size
        self.table = np.ones(table_size, dtype=np.int8) * 2  # Initialize to Weakly Taken

    def fit(self, X: pd.DataFrame, y: pd.Series):
        pc_indices = X["pc_idx"].values
        outcomes = y.values
        for pc_idx, actual in zip(pc_indices, outcomes):
            idx = int(pc_idx) % self.table_size
            curr = self.table[idx]
            if actual == 1:
                self.table[idx] = min(3, curr + 1)
            else:
                self.table[idx] = max(0, curr - 1)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pc_indices = X["pc_idx"].values
        return (self.table[pc_indices % self.table_size] >= 2).astype(int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        proba = np.zeros((len(preds), 2))
        proba[:, 1] = preds * 0.8 + (1 - preds) * 0.2
        proba[:, 0] = 1.0 - proba[:, 1]
        return proba


class GsharePredictor:
    """Hardware Gshare Branch Predictor (PC XOR Global History)."""
    def __init__(self, table_size: int = DEFAULT_PC_MOD, hist_bits: int = DEFAULT_HIST_LEN):
        self.table_size = table_size
        self.hist_bits = hist_bits
        self.table = np.ones(table_size, dtype=np.int8) * 2

    def _hash(self, pc: int, history_bits: np.ndarray) -> int:
        hist_val = 0
        for b in history_bits:
            hist_val = (hist_val << 1) | int(b)
        return (pc ^ (hist_val & (self.table_size - 1))) % self.table_size

    def fit(self, X: pd.DataFrame, y: pd.Series):
        hist_cols = [f"h{k}" for k in range(1, self.hist_bits + 1)]
        pcs = X["pc_idx"].values
        hists = X[hist_cols].values
        outcomes = y.values

        for pc, hist, actual in zip(pcs, hists, outcomes):
            idx = self._hash(int(pc), hist)
            curr = self.table[idx]
            if actual == 1:
                self.table[idx] = min(3, curr + 1)
            else:
                self.table[idx] = max(0, curr - 1)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        hist_cols = [f"h{k}" for k in range(1, self.hist_bits + 1)]
        pcs = X["pc_idx"].values
        hists = X[hist_cols].values
        preds = np.zeros(len(pcs), dtype=int)
        for i, (pc, hist) in enumerate(zip(pcs, hists)):
            idx = self._hash(int(pc), hist)
            preds[i] = 1 if self.table[idx] >= 2 else 0
        return preds

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        proba = np.zeros((len(preds), 2))
        proba[:, 1] = preds * 0.85 + (1 - preds) * 0.15
        proba[:, 0] = 1.0 - proba[:, 1]
        return proba


class PerceptronPredictor:
    """Jiménez & Lin Perceptron Neural Branch Predictor."""
    def __init__(self, table_size: int = DEFAULT_PC_MOD, hist_len: int = DEFAULT_HIST_LEN, theta: int = 35):
        self.table_size = table_size
        self.hist_len = hist_len
        self.theta = theta
        self.weights = np.zeros((table_size, hist_len + 1), dtype=np.float32)

    def fit(self, X: pd.DataFrame, y: pd.Series):
        hist_cols = [f"h{k}" for k in range(1, self.hist_len + 1)]
        pcs = X["pc_idx"].values
        hists = np.where(X[hist_cols].values == 1, 1.0, -1.0)
        outcomes = np.where(y.values == 1, 1.0, -1.0)

        for pc, hist, t in zip(pcs, hists, outcomes):
            idx = int(pc) % self.table_size
            w = self.weights[idx]
            y_out = w[0] + np.dot(w[1:], hist)
            y_pred = 1.0 if y_out >= 0 else -1.0

            if (y_pred != t) or (abs(y_out) <= self.theta):
                w[0] += t
                w[1:] += t * hist
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        hist_cols = [f"h{k}" for k in range(1, self.hist_len + 1)]
        pcs = X["pc_idx"].values
        hists = np.where(X[hist_cols].values == 1, 1.0, -1.0)
        preds = np.zeros(len(pcs), dtype=int)

        for i, (pc, hist) in enumerate(zip(pcs, hists)):
            idx = int(pc) % self.table_size
            w = self.weights[idx]
            y_out = w[0] + np.dot(w[1:], hist)
            preds[i] = 1 if y_out >= 0 else 0
        return preds

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        hist_cols = [f"h{k}" for k in range(1, self.hist_len + 1)]
        pcs = X["pc_idx"].values
        hists = np.where(X[hist_cols].values == 1, 1.0, -1.0)
        proba = np.zeros((len(pcs), 2))

        for i, (pc, hist) in enumerate(zip(pcs, hists)):
            idx = int(pc) % self.table_size
            w = self.weights[idx]
            y_out = w[0] + np.dot(w[1:], hist)
            p1 = 1.0 / (1.0 + np.exp(-np.clip(y_out / 10.0, -20, 20)))
            proba[i, 1] = p1
            proba[i, 0] = 1.0 - p1
        return proba
