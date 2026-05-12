"""
Hot reload wrapper for VieNeu-TTS Gradio app.
Automatically restarts the server when code changes are detected.
"""
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_callback):
        self.restart_callback = restart_callback
        self.last_restart = 0

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # Debounce: only restart if 2 seconds have passed
            current_time = time.time()
            if current_time - self.last_restart > 2:
                print(f"\n[RELOAD] Detected change in {event.src_path}")
                print("[RELOAD] Restarting server...")
                self.last_restart = current_time
                self.restart_callback()

def run_server():
    """Start the Gradio server."""
    return subprocess.Popen(
        [sys.executable, "apps/gradio_persistent.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1
    )

def main():
    print("Starting VieNeu-TTS with hot reload...")
    print("Watching for changes in apps/ directory")
    print("Press Ctrl+C to stop\n")

    process = None

    def restart_server():
        nonlocal process
        if process:
            print("[STOP] Stopping current server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        print("[START] Starting new server...")
        process = run_server()

        # Print server output in background
        def print_output():
            for line in process.stdout:
                try:
                    print(line, end='')
                except UnicodeEncodeError:
                    # Skip lines with encoding issues
                    pass

        import threading
        threading.Thread(target=print_output, daemon=True).start()

    # Start initial server
    restart_server()

    # Set up file watcher
    event_handler = CodeChangeHandler(restart_server)
    observer = Observer()
    observer.schedule(event_handler, path="apps", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[STOP] Stopping server...")
        observer.stop()
        if process:
            process.terminate()

    observer.join()
    print("[DONE] Server stopped")

if __name__ == "__main__":
    main()
