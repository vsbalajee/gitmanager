import logging
import streamlit as st
from datetime import datetime
import os

class AppLogger:
    def __init__(self, name="GitHubRepoManager"):
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """Setup logger with file and console handlers"""
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Set log level from secrets or default to INFO
            log_level = st.secrets.get("app", {}).get("log_level", "INFO")
            self.logger.setLevel(getattr(logging, log_level))
            
            # Prevent duplicate handlers
            if not self.logger.handlers:
                # File handler
                file_handler = logging.FileHandler(
                    f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
                )
                file_handler.setLevel(logging.DEBUG)
                
                # Console handler
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                
                # Formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                
                # Add handlers
                self.logger.addHandler(file_handler)
                self.logger.addHandler(console_handler)
                
        except Exception as e:
            st.error(f"Failed to setup logger: {str(e)}")
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def debug(self, message):
        self.logger.debug(message)

# Global logger instance
logger = AppLogger()