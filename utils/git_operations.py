import os
import git
import shutil
import streamlit as st
from pathlib import Path
from utils.logger import logger
import tempfile
import subprocess

class GitOperations:
    def __init__(self):
        self.temp_dirs = []
    
    def clone_repository(self, clone_url, local_path, repo_name, progress_callback=None):
        """Clone a repository to local path"""
        try:
            # Ensure local path exists
            os.makedirs(local_path, exist_ok=True)
            
            # Full path for the repository
            repo_path = os.path.join(local_path, repo_name)
            
            # Check if directory already exists
            if os.path.exists(repo_path):
                if os.listdir(repo_path):  # Directory is not empty
                    raise Exception(f"Directory '{repo_path}' already exists and is not empty")
            
            logger.info(f"Cloning repository to: {repo_path}")
            
            # Clone the repository
            if progress_callback:
                progress_callback(0, "Starting clone...")
            
            repo = git.Repo.clone_from(
                clone_url, 
                repo_path,
                progress=self._create_progress_handler(progress_callback) if progress_callback else None
            )
            
            if progress_callback:
                progress_callback(100, "Clone completed!")
            
            logger.info(f"Successfully cloned repository to: {repo_path}")
            return repo_path
            
        except git.exc.GitCommandError as e:
            error_msg = f"Git command failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error cloning repository: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _create_progress_handler(self, callback):
        """Create a progress handler for git operations"""
        def progress_handler(op_code, cur_count, max_count=None, message=''):
            if max_count:
                percentage = int((cur_count / max_count) * 100)
                callback(percentage, f"Cloning... {percentage}%")
        return progress_handler
    
    def initialize_and_push(self, local_path, repo_url, commit_message="Initial commit"):
        """Initialize git repo and push to GitHub"""
        try:
            logger.info(f"Initializing git repository at: {local_path}")
            
            # Initialize git repository
            repo = git.Repo.init(local_path)
            
            # Add all files
            repo.git.add(A=True)
            
            # Check if there are any changes to commit
            if repo.is_dirty() or repo.untracked_files:
                # Commit changes
                repo.index.commit(commit_message)
                
                # Add remote origin
                origin = repo.create_remote('origin', repo_url)
                
                # Push to remote
                origin.push(refspec='HEAD:main')
                
                logger.info(f"Successfully pushed repository to: {repo_url}")
                return True
            else:
                logger.warning("No changes to commit")
                return False
                
        except git.exc.GitCommandError as e:
            error_msg = f"Git command failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error initializing and pushing repository: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def validate_git_installation(self):
        """Validate that git is installed and accessible"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Git installation validated: {result.stdout.strip()}")
                return True, result.stdout.strip()
            else:
                error_msg = "Git is not properly installed or accessible"
                logger.error(error_msg)
                return False, error_msg
        except subprocess.TimeoutExpired:
            error_msg = "Git command timed out"
            logger.error(error_msg)
            return False, error_msg
        except FileNotFoundError:
            error_msg = "Git is not installed or not in PATH"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error validating git installation: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_directory_size(self, path):
        """Get the size of a directory"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception as e:
            logger.error(f"Error calculating directory size: {str(e)}")
            return 0
    
    def cleanup_temp_dirs(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {str(e)}")
        self.temp_dirs.clear()