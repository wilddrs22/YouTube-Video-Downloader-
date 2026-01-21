import os
from datetime import datetime
from android.storage import app_storage_path

# Use app-specific storage for logs and progress
try:
    APP_DIR = app_storage_path()
except:
    APP_DIR = '/data/data/org.yourapp.ytdownloader/files'

LOG_FILE = os.path.join(APP_DIR, "download.log")
PROGRESS_FILE = os.path.join(APP_DIR, "progress.txt")

def log(message):
    """Write log message to file"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Logging error: {e}")

def write_progress(message):
    """Write progress update to file"""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(message)
    except Exception as e:
        print(f"Progress write error: {e}")

def get_progress():
    """Read current progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "Waiting..."
    except Exception as e:
        return f"Error reading progress: {e}"

def clear_progress():
    """Clear the progress file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
    except Exception as e:
        print(f"Clear progress error: {e}")
