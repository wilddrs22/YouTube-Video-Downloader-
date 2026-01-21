
import os
from datetime import datetime

# Try Android imports
try:
    from android.storage import app_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

def get_app_dir():
    """Get app-specific storage directory"""
    if ANDROID:
        try:
            return app_storage_path()
        except:
            return '/data/data/org.wilddrs.ytdownloader/files'
    else:
        # Desktop fallback
        return os.path.expanduser('~/.ytdownloader')

# Use app-specific storage for logs and progress
APP_DIR = get_app_dir()

# Create app directory if it doesn't exist
try:
    os.makedirs(APP_DIR, exist_ok=True)
except:
    pass

LOG_FILE = os.path.join(APP_DIR, "download.log")
PROGRESS_FILE = os.path.join(APP_DIR, "progress.txt")

# Initialize log file on first import
try:
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"App started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"App directory: {APP_DIR}\n")
        f.write(f"Android mode: {ANDROID}\n")
        f.write(f"{'='*60}\n\n")
except Exception as e:
    print(f"Could not initialize log file: {e}")

def log(message):
    """Write log message to file and console"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Write to file
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
        
        # Also print to console
        print(log_message)
    except Exception as e:
        print(f"Logging error: {e} - Message was: {message}")

def write_progress(message):
    """Write progress update to file"""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(message)
    except Exception as e:
        print(f"Progress write error: {e}")
        log(f"Progress write error: {e}")

def get_progress():
    """Read current progress from file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content if content else "Waiting..."
        return "Waiting..."
    except Exception as e:
        log(f"Error reading progress: {e}")
        return "Error reading progress"

def clear_progress():
    """Clear the progress file"""
    try:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            log("Progress file cleared")
    except Exception as e:
        print(f"Clear progress error: {e}")
        log(f"Clear progress error: {e}")

def get_log_content(lines=50):
    """Get the last N lines from the log file"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        return "No log file found"
    except Exception as e:
        return f"Error reading log: {e}"

def clear_logs():
    """Clear all log files"""
    try:
        for file in [LOG_FILE, PROGRESS_FILE]:
            if os.path.exists(file):
                os.remove(file)
        log("All logs cleared")
        return True
    except Exception as e:
        print(f"Error clearing logs: {e}")
        return False

# Log system info on import
log(f"Debug module initialized")
log(f"Log file: {LOG_FILE}")
log(f"Progress file: {PROGRESS_FILE}")
