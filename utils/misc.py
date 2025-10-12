import os
import threading
import shutil
import re
import glob
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config

from utils.loggers import get_logger

log = get_logger(__name__)

class LoadoutSnapshotter(FileSystemEventHandler):
    """
    LoadoutSnapshotter is a file system event handler that monitors a specified directory for file modifications and automatically creates timestamped snapshot copies of modified files. It retains only a configurable maximum number of recent snapshots per file, cleaning up older ones as needed.
    This utility is useful for tracking changes to files in real-time, providing a simple versioning mechanism by storing historical copies with timestamps. It leverages watchdog's Observer to monitor file system events and handles snapshot management transparently.
        monitor_dir (Path): The directory being monitored for file changes and where snapshots are stored.
        observer (Observer or None): The watchdog observer instance managing directory monitoring.
        timestamp_pattern (re.Pattern): Compiled regular expression to identify snapshot files by their timestamped names.
        max_snapshots (int): The maximum number of snapshots to retain for each file.
    Methods:
        __init__(monitor_dir: str, max_snapshots: int = 10):
            Initializes the snapshotter, prepares the monitoring directory, and sets up internal state.
        _cleanup_old_snapshots(original_file_path: Path) -> None:
            Removes older snapshot files for a given original file, keeping only the most recent up to max_snapshots.
        on_modified(event) -> None:
            Handles file modification events by creating a timestamped snapshot and cleaning up old snapshots.
        start() -> None:
            Starts monitoring the specified directory for file changes.
        stop() -> None:
            Stops monitoring the directory and cleans up the observer.
    """
    
    def __init__(self, monitor_dir: str, max_snapshots: int = 10) -> None:
        """
        Initializes the monitoring utility.
        Args:
            monitor_dir (str): The directory to monitor and store snapshots.
            max_snapshots (int, optional): The maximum number of snapshots to retain. Defaults to 10.
        Attributes:
            monitor_dir (Path): Path object for the monitored directory.
            observer: Placeholder for the directory observer instance.
            timestamp_pattern (re.Pattern): Compiled regex pattern to match timestamped filenames.
            max_snapshots (int): Maximum number of snapshots to keep.
        """
        
        self.monitor_dir = Path(monitor_dir)
        self.monitor_dir.mkdir(parents=True, exist_ok=True)
        self.observer = None
        
        # Pattern to match our timestamp format
        self.timestamp_pattern = re.compile(config.SNAPSHOT_PATTERN)
        self.max_snapshots = max_snapshots

    def _cleanup_old_snapshots(self, original_file_path: Path) -> None:
        """
        Removes old snapshot files associated with the given original file, keeping only the most recent snapshots up to `self.max_snapshots`.
        This method searches for snapshot files in the same directory as the original file, matching a specific timestamp pattern in their names. It sorts the valid snapshots by modification time (newest first) and deletes the oldest ones if their count exceeds `self.max_snapshots`.
        Args:
            original_file_path (Path): The path to the original file whose snapshots are to be managed.
        Raises:
            Logs errors if any snapshot file cannot be removed.
        """
        
        file_stem = original_file_path.stem
        file_suffix = original_file_path.suffix
        parent_dir = original_file_path.parent
        
        # Find all snapshot files for this original file
        pattern = f"{file_stem}_*{file_suffix}"
        snapshot_files = list(parent_dir.glob(pattern))
        
        # Filter to only include files that match our timestamp pattern
        valid_snapshots = [f for f in snapshot_files if self.timestamp_pattern.search(f.stem)]
        
        # Sort by modification time (newest first)
        valid_snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove excess snapshots
        if len(valid_snapshots) > self.max_snapshots:
            for old_snapshot in valid_snapshots[self.max_snapshots:]:
                try:
                    old_snapshot.unlink()
                    log.info(f"Removed old snapshot: {old_snapshot}")
                except Exception as e:
                    log.error(f"Failed to remove old snapshot {old_snapshot}: {e}")

    def on_modified(self, event) -> None:
        """
        Handles file modification events by creating a timestamped snapshot of the modified file,
        unless the file is already a snapshot. Also triggers cleanup of old snapshots for the file.
        Args:
            event: The file system event object containing information about the modified file.
        Returns:
            None
        Logs:
            - Info message when a snapshot is created.
            - Error message if snapshot creation fails.
        """
        
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Skip if this is already a snapshot file
        if self.timestamp_pattern.search(file_path.stem):
            return
        
        try:
            timestamp = datetime.now().strftime(config.SNAPSHOT_FORMAT)
            snapshot_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            snapshot_path = file_path.parent / snapshot_name
            
            shutil.copy2(file_path, snapshot_path)
            log.info(f"Created snapshot: {snapshot_path}")
            
            # Clean up old snapshots
            self._cleanup_old_snapshots(file_path)
            
        except Exception as e:
            log.error(f"Failed to create snapshot for {event.src_path}: {e}")

    def start(self) -> None:
        """
        Starts monitoring the specified directory for file system changes.

        If the observer is not already running, this method initializes an Observer,
        schedules it to watch the target directory recursively, and starts the observer.
        Logs a message indicating that monitoring has started.

        Returns:
            None
        """
        
        if self.observer is None:
            self.observer = Observer()
            self.observer.schedule(self, str(self.monitor_dir), recursive=True)
            self.observer.start()
            log.info(f"Started monitoring directory: {self.monitor_dir}")

    def stop(self) -> None:
        """
        Stops the directory monitoring process if it is currently running.

        This method stops the observer thread responsible for monitoring a directory,
        waits for it to finish, and then cleans up the observer reference. It also logs
        that monitoring has been stopped.
        """
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            log.info("Stopped monitoring directory")