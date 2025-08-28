import streamlit as st
from github import Github, GithubException
from utils.logger import logger
import re
import time

class GitHubAuth:
    def __init__(self):
        self.github_client = None
    
    def validate_pat_format(self, token):
        """Validate GitHub PAT format"""
        try:
            # GitHub PAT patterns
            classic_pattern = r'^ghp_[a-zA-Z0-9]{36}$'
            fine_grained_pattern = r'^github_pat_[a-zA-Z0-9_]{82}$'
            
            if re.match(classic_pattern, token) or re.match(fine_grained_pattern, token):
                return True
            return False
        except Exception as e:
            logger.error(f"Error validating PAT format: {str(e)}")
            return False
    
    def authenticate(self, token):
        """Authenticate with GitHub using PAT"""
        try:
            if not token:
                logger.warning("Empty token provided")
                return False, "Token cannot be empty"
            
            # Clean the token (remove any whitespace)
            token = token.strip()
            
            if not self.validate_pat_format(token):
                logger.warning("Invalid PAT format provided")
                return False, "Invalid GitHub PAT format"
            
            # Test authentication with timeout and retry
            github_client = Github(token, timeout=30, retry=3)
            user = github_client.get_user()
            
            # Test basic permissions with proper error handling
            try:
                login = user.login
                name = user.name
                logger.info(f"Authentication successful for user: {login}")
            except Exception as e:
                logger.error(f"Failed to get user details: {str(e)}")
                return False, "Token is valid but cannot access user information"
            
            self.github_client = github_client
            logger.info(f"Successfully authenticated user: {login}")
            
            return True, f"Successfully authenticated as {login}"
            
        except GithubException as e:
            if hasattr(e, 'data') and e.data:
                error_msg = f"GitHub authentication failed: {e.data.get('message', str(e))}"
            else:
                error_msg = f"GitHub authentication failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            if "rate limit" in str(e).lower():
                error_msg = "GitHub API rate limit exceeded. Please try again later."
            elif "network" in str(e).lower() or "timeout" in str(e).lower():
                error_msg = "Network error. Please check your internet connection."
            else:
                error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_connection(self):
        """Test GitHub connection without authentication"""
        try:
            # Test basic GitHub connectivity
            github_client = Github(timeout=10)
            # Try to access a public endpoint
            github_client.get_rate_limit()
            return True, "GitHub connection successful"
        except Exception as e:
            error_msg = f"Cannot connect to GitHub: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_user_info(self):
        """Get authenticated user information"""
        try:
            if not self.github_client:
                return None
            
            user = self.github_client.get_user()
            return {
                'login': user.login,
                'name': user.name or user.login,
                'email': user.email,
                'public_repos': user.public_repos,
                'private_repos': user.total_private_repos,
                'avatar_url': user.avatar_url
            }
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    def get_github_client(self):
        """Get the authenticated GitHub client"""
        return self.github_client

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'github_auth' not in st.session_state:
        st.session_state.github_auth = GitHubAuth()
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'developer_name' not in st.session_state:
        st.session_state.developer_name = ""
    if 'github_token' not in st.session_state:
        st.session_state.github_token = ""