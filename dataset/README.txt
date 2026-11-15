data/raw_dataset.csv        trace_num, branch_index, pc, taken  (per-branch trace table; 10 traces x 20,016 branches)
preprocess.py               raw_dataset.csv -> processed_dataset.csv   (run: python preprocess.py)
data/processed_dataset.csv  ML-ready: pc_idx, h1..h16 (features), label (target), split (0/1/2)
Do NOT use as features: trace_num, branch_index, split
Note: raw_dataset.csv was rebuilt from the processed data; the first 16 branches of each trace have no pc (blank).
