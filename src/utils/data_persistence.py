# app/utils/data_persistence.py
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("tamu_newsletter")

class DataPersistence:
    """Utility class for saving and loading event data"""
    
    def __init__(self, events_file: str = "events.json", backup_dir: str = "backups"):
        """
        Initialize data persistence manager
        
        Args:
            events_file: Path to main events JSON file
            backup_dir: Directory to store backup files
        """
        self.events_file = events_file
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def save_events_data(self, events_data: Dict[str, Any], create_backup: bool = True) -> bool:
        """
        Save events data to file
        
        Args:
            events_data: Events data dictionary
            create_backup: Whether to create a backup of existing file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested and file exists
            if create_backup and Path(self.events_file).exists():
                self._create_backup()
            
            # Save the data
            with open(self.events_file, "w", encoding="utf-8") as f:
                json.dump(events_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved events data to {self.events_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving events data: {e}")
            return False
    
    def load_events_data(self) -> Optional[Dict[str, Any]]:
        """
        Load events data from file
        
        Returns:
            Events data dictionary or None if failed
        """
        try:
            if not Path(self.events_file).exists():
                logger.warning(f"Events file {self.events_file} does not exist")
                return None
            
            with open(self.events_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            logger.info(f"Successfully loaded events data from {self.events_file}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading events data: {e}")
            return None
    
    def _create_backup(self) -> bool:
        """
        Create a backup of the current events file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import datetime
            import shutil
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"events_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(self.events_file, backup_path)
            logger.info(f"Created backup: {backup_path}")
            
            # Keep only the last 10 backups
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """
        Remove old backup files, keeping only the most recent ones
        
        Args:
            keep_count: Number of backup files to keep
        """
        try:
            backup_files = list(self.backup_dir.glob("events_backup_*.json"))
            
            if len(backup_files) > keep_count:
                # Sort by modification time (oldest first)
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                
                # Remove oldest files
                for old_backup in backup_files[:-keep_count]:
                    old_backup.unlink()
                    logger.info(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def get_backup_files(self) -> list:
        """
        Get list of available backup files
        
        Returns:
            List of backup file paths, sorted by date (newest first)
        """
        try:
            backup_files = list(self.backup_dir.glob("events_backup_*.json"))
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return backup_files
            
        except Exception as e:
            logger.error(f"Error getting backup files: {e}")
            return []
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore events data from a backup file
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import shutil
            
            # Create backup of current file first
            self._create_backup()
            
            # Restore from backup
            shutil.copy2(backup_path, self.events_file)
            logger.info(f"Restored events data from backup: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False