"""
Pipeline2 - Application Configuration
Centralized path definitions and server settings.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "raw_dataset.csv")
PROCESSED_DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "processed_dataset.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "ml", "model")

DEFAULT_PORT = 5000
DEFAULT_HOST = "0.0.0.0"
