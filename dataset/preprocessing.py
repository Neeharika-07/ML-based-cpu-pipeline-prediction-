"""
PipelineAI - Data Preprocessing Script (Member 2)
Description:
    Cleans the raw text dataset (raw_dataset.csv) and converts it to pure numbers (processed_dataset.csv).
    Implements the 5 required tasks in order:
    1. Parse Instructions into Opcode, Dest, Src1, Src2
    2. Handle Missing Values (drop empty rows)
    3. Extract Register Numbers (strip 'R')
    4. Create Hazard Feature (Is_Same_Register)
    5. Encode Text to Numbers using Label Encoding

Output Columns:
    Opcode_1, Opcode_2, Dest_Reg_1, Src_Reg_1_Inst2, Src_Reg_2_Inst2,
    Is_Same_Register, Is_Load_Inst1, Distance, Conflict_Type_Label
"""

import os
import re
import sys
import time                                                                                                                                                                                                      vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
import argparse
import pandas as pd


# 1. Opcode Mapping (ADD=0, SUB=1, LOAD=2, STORE=3, etc.)
OPCODE_MAP = {
    'ADD': 0,
    'SUB': 1,
    'LOAD': 2,
    'STORE': 3,
    'MUL': 4,
    'DIV': 5,
    'AND': 6,
    'OR': 7,
    'XOR': 8,
    'SHIFT': 9
}

# 2. Conflict Type Mapping (No Hazard=0, RAW=1, WAR=2, WAW=3)
CONFLICT_MAP = {
    'NO HAZARD': 0,
    'NO_HAZARD': 0,
    'NONE': 0,
    'RAW': 1,
    'WAR': 2,
    'WAW': 3
}


def clean_register(reg_token: str) -> int:
    """
    Extracts the integer register number from a register string.
    Example: 'R1' -> 1, 'R15' -> 15.
    If plain integer string: parses directly.
    """
    token = str(reg_token).strip()
    if token.upper().startswith('R'):
        digits = token[1:]
        if digits.isdigit():
            return int(digits)
    # If integer
    match = re.search(r'\d+', token)
    if match:
        return int(match.group())
    return 0


def parse_instruction(inst_str: str) -> dict:
    """
    Splits an instruction into Opcode, Dest, Src1, and Src2.
    Handles:
    - Arithmetic / Logical: 'ADD R1, R2, R3' -> Opcode=ADD, Dest=1, Src1=2, Src2=3
    - Load / Store:         'LOAD R1, 0(R2)' -> Opcode=LOAD, Dest=1, Src1=2, Src2=0
    - Load / Store:         'STORE R2, 0(R5)' -> Opcode=STORE, Dest=2, Src1=5, Src2=0
    """
    cleaned = str(inst_str).strip()
    if not cleaned:
        raise ValueError("Empty instruction")

    parts = cleaned.split(maxsplit=1)
    opcode = parts[0].strip().upper()
    operands_str = parts[1].strip() if len(parts) > 1 else ""

    opcode_id = OPCODE_MAP.get(opcode, 0)
    dest_reg = 0
    src1_reg = 0
    src2_reg = 0

    # Check for offset(register) syntax: e.g. LOAD R1, 0(R2) or STORE R2, 0(R5)
    mem_match = re.search(r'([Rr]?\d+)\s*,\s*(\d*)\s*\(([Rr]?\d+)\)', operands_str)
    if mem_match:
        dest_reg = clean_register(mem_match.group(1))
        offset = int(mem_match.group(2)) if mem_match.group(2) else 0
        src1_reg = clean_register(mem_match.group(3))
        src2_reg = offset
    else:
        # Standard comma-separated operands
        tokens = [t.strip() for t in operands_str.split(',') if t.strip()]
        if len(tokens) >= 1:
            dest_reg = clean_register(tokens[0])
        if len(tokens) >= 2:
            src1_reg = clean_register(tokens[1])
        if len(tokens) >= 3:
            src2_reg = clean_register(tokens[2])

    return {
        'opcode_str': opcode,
        'opcode_id': opcode_id,
        'dest': dest_reg,
        'src1': src1_reg,
        'src2': src2_reg
    }


def preprocess_dataset(input_csv: str, output_csv: str) -> pd.DataFrame:
    """
    Processes raw_dataset.csv into processed_dataset.csv adhering strictly
    to the 5 required steps and generating the exact 9 numerical columns.
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    print(f"[*] Step 1 & 2: Loading raw dataset and handling missing values: {input_csv}")
    raw_df = pd.read_csv(input_csv)
    initial_count = len(raw_df)

    # Step 2: Handle Missing Values - delete any empty row
    raw_df = raw_df.dropna(subset=['Instruction_1', 'Instruction_2'])
    raw_df = raw_df[raw_df['Instruction_1'].str.strip() != '']
    raw_df = raw_df[raw_df['Instruction_2'].str.strip() != '']
    print(f"[*] Retained {len(raw_df):,} of {initial_count:,} rows after dropping missing values.")

    processed_rows = []

    for idx, row in raw_df.iterrows():
        # Step 1 & 3: Parse Instructions and extract register numbers
        i1 = parse_instruction(row['Instruction_1'])
        i2 = parse_instruction(row['Instruction_2'])

        opcode_1 = i1['opcode_id']
        opcode_2 = i2['opcode_id']
        dest_reg_1 = i1['dest']
        src_reg_1_inst2 = i2['src1']
        src_reg_2_inst2 = i2['src2']

        # Step 4: Create Hazard Feature (Is_Same_Register)
        # If Dest of Instruction_1 == Src of Instruction_2 (either src1 or src2), put 1, else 0
        if dest_reg_1 == src_reg_1_inst2 or dest_reg_1 == src_reg_2_inst2:
            is_same_register = 1
        else:
            is_same_register = 0

        # Additional required pipeline features
        is_load_inst1 = 1 if i1['opcode_str'] == 'LOAD' else 0
        distance = 1  # Consecutive instructions in pipeline

        # Step 5: Encode Text to Numbers using Label Encoding
        conflict_raw = str(row['Conflict_Type']).strip().upper()
        conflict_label = CONFLICT_MAP.get(conflict_raw, 0)

        processed_rows.append({
            'Opcode_1': opcode_1,
            'Opcode_2': opcode_2,
            'Dest_Reg_1': dest_reg_1,
            'Src_Reg_1_Inst2': src_reg_1_inst2,
            'Src_Reg_2_Inst2': src_reg_2_inst2,
            'Is_Same_Register': is_same_register,
            'Is_Load_Inst1': is_load_inst1,
            'Distance': distance,
            'Conflict_Type_Label': conflict_label
        })

    processed_df = pd.DataFrame(processed_rows)

    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    processed_df.to_csv(output_csv, index=False)

    print(f"[+] Output successfully generated at: {output_csv}")
    print(f"[+] Total rows: {len(processed_df)}")
    print(f"[+] Columns ({len(processed_df.columns)}): {list(processed_df.columns)}")

    return processed_df


def main():
    parser = argparse.ArgumentParser(description="Member 2 Preprocessing Pipeline")
    parser.add_argument('--input', '-i', type=str, default='dataset/raw_dataset.csv', help="Path to raw_dataset.csv")
    parser.add_argument('--output', '-o', type=str, default='dataset/processed_dataset.csv', help="Path to processed_dataset.csv")
    args = parser.parse_args()

    # Resolve paths relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) if os.path.basename(script_dir) == 'ml' else script_dir

    input_path = os.path.abspath(os.path.join(project_root, args.input)) if not os.path.isabs(args.input) else args.input
    output_path = os.path.abspath(os.path.join(project_root, args.output)) if not os.path.isabs(args.output) else args.output

    start_time = time.time()
    preprocess_dataset(input_path, output_path)
    elapsed = time.time() - start_time
    print(f"[+] Preprocessing finished in {elapsed:.2f} seconds.")


if __name__ == '__main__':
    main()
