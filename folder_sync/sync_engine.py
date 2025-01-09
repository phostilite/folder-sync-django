# folder_sync/sync_engine.py
import os
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread, Event
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FolderSyncHandler(FileSystemEventHandler):
    def __init__(self, main_folder, target_folders):
        self.main_folder = main_folder
        self.target_folders = target_folders
        self.sync_event = Event()
        super().__init__()
        logger.info(f"Initializing sync handler for {main_folder} -> {target_folders}")

    def _get_relative_path(self, absolute_path):
        return os.path.relpath(absolute_path, self.main_folder)

    def _sync_to_targets(self, src_path, is_delete=False):
        relative_path = self._get_relative_path(src_path)
        operation = "deleting" if is_delete else "syncing"
        logger.info(f"Starting {operation} operation for: {src_path}")
        start_time = time.time()
        
        for target in self.target_folders:
            target_path = os.path.join(target, relative_path)
            logger.debug(f"Processing target: {target_path}")
            
            try:
                if is_delete:
                    if os.path.exists(target_path):
                        if os.path.isdir(target_path):
                            logger.info(f"Removing directory: {target_path}")
                            shutil.rmtree(target_path)
                        else:
                            logger.info(f"Removing file: {target_path}")
                            os.remove(target_path)
                else:
                    if os.path.isdir(src_path):
                        if not os.path.exists(target_path):
                            logger.info(f"Copying directory: {src_path} -> {target_path}")
                            shutil.copytree(src_path, target_path)
                    else:
                        logger.info(f"Copying file: {src_path} -> {target_path}")
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.copy2(src_path, target_path)
                
                end_time = time.time()
                logger.info(f"Operation completed in {end_time - start_time:.2f} seconds")
                
            except Exception as e:
                logger.exception(f"Error during {operation} operation")
                raise

    def on_created(self, event):
        if not event.is_directory and not event.src_path.endswith('.tmp'):
            logger.info(f"File creation detected: {event.src_path}")
            logger.info(f"Timestamp: {datetime.now().isoformat()}")
            self._sync_to_targets(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and not event.src_path.endswith('.tmp'):
            logger.info(f"File modification detected: {event.src_path}")
            logger.info(f"Timestamp: {datetime.now().isoformat()}")
            self._sync_to_targets(event.src_path)

    def on_deleted(self, event):
        logger.info(f"Deletion detected: {event.src_path}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        self._sync_to_targets(event.src_path, is_delete=True)

class FolderSyncEngine:
    def __init__(self):
        self.observer = None
        self.handler = None
        self.is_running = False

    def _perform_initial_sync(self, main_folder, target_folders):
        logger.info("Starting initial sync of existing content...")
        start_time = time.time()

        try:
            # Walk through all files and directories in main folder
            for root, dirs, files in os.walk(main_folder):
                # Calculate relative path
                relative_path = os.path.relpath(root, main_folder)
                
                # Create directories in all targets
                for target in target_folders:
                    target_dir = os.path.join(target, relative_path)
                    if not os.path.exists(target_dir):
                        logger.info(f"Creating directory: {target_dir}")
                        os.makedirs(target_dir, exist_ok=True)

                # Copy all files
                for file in files:
                    source_file = os.path.join(root, file)
                    for target in target_folders:
                        target_file = os.path.join(target, relative_path, file)
                        if not os.path.exists(target_file):
                            logger.info(f"Copying file: {source_file} -> {target_file}")
                            shutil.copy2(source_file, target_file)

            end_time = time.time()
            logger.info(f"Initial sync completed in {end_time - start_time:.2f} seconds")

        except Exception as e:
            logger.exception("Error during initial sync")
            raise Exception(f"Initial sync failed: {str(e)}")

    def start_sync(self, main_folder, target_folders):
        logger.info(f"=== Starting Folder Sync Engine ===")
        logger.info(f"Main folder: {main_folder}")
        logger.info(f"Target folders: {target_folders}")
        logger.info(f"Start time: {datetime.now().isoformat()}")
        
        if self.is_running:
            logger.info("Stopping existing sync before starting new one")
            self.stop_sync()

        # Perform initial sync of existing content
        self._perform_initial_sync(main_folder, target_folders)

        # Start watching for changes
        self.handler = FolderSyncHandler(main_folder, target_folders)
        self.observer = Observer()
        self.observer.schedule(self.handler, main_folder, recursive=True)
        self.observer.start()
        self.is_running = True
        logger.info(f"Started watching for changes")

    def stop_sync(self):
        if self.observer:
            logger.info("=== Stopping Folder Sync Engine ===")
            logger.info(f"Stop time: {datetime.now().isoformat()}")
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("Sync engine stopped successfully")