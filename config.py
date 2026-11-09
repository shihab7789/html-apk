
import os
from pathlib import Path
DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp/apk-server-data"))
UPLOAD_DIR, WORK_DIR, OUTPUT_DIR = DATA_DIR/"uploads", DATA_DIR/"work", DATA_DIR/"outputs"
DB_PATH = DATA_DIR/"jobs.sqlite3"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
MAX_EXTRACTED_MB = int(os.getenv("MAX_EXTRACTED_MB", "80"))
MAX_FILES = int(os.getenv("MAX_FILES", "300"))
BUILD_TIMEOUT = int(os.getenv("BUILD_TIMEOUT", "900"))
for p in (UPLOAD_DIR, WORK_DIR, OUTPUT_DIR): p.mkdir(parents=True, exist_ok=True)
