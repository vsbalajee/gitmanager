import streamlit as st
from github import Github, GithubException
from utils.logger import logger
import os
from datetime import datetime
import time

class GitHubManager:
    def __init__(self, github_client):
        if not github_client:
            raise ValueError("GitHub client cannot be None")
        self.github_client = github_client
        self.user = None
        self._initialize_user()
    
    def _initialize_user(self):
        """Initialize user object"""
        try:
            self.user = self.github_client.get_user()
        except Exception as e:
            logger.error(f"Failed to initialize user: {str(e)}")
            raise
    
    def get_repositories(self, repo_type="all"):
        """Get user repositories"""
        try:
            if not self.github_client:
                raise Exception("GitHub client not initialized")
                
            logger.info(f"Fetching repositories of type: {repo_type}")
            
            # Add retry logic for API calls
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if repo_type == "public":
                        repos = self.user.get_repos(type="public")
                    elif repo_type == "private":
                        repos = self.user.get_repos(type="private")
                    else:
                        repos = self.user.get_repos(type="all")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
            
            repo_list = []
            for repo in repos:
                try:
                    repo_info = {
                        'name': repo.name,
                        'full_name': repo.full_name,
                        'description': repo.description or "No description",
                        'private': repo.private,
                        'clone_url': repo.clone_url,
                        'ssh_url': repo.ssh_url,
                        'html_url': repo.html_url,
                        'language': repo.language,
                        'size': repo.size,
                        'stars': repo.stargazers_count,
                        'forks': repo.forks_count,
                        'updated_at': repo.updated_at,
                        'created_at': repo.created_at,
                        'default_branch': repo.default_branch
                    }
                    repo_list.append(repo_info)
                except Exception as e:
                    logger.warning(f"Error processing repo {repo.name}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(repo_list)} repositories")
            return repo_list
            
        except GithubException as e:
            if hasattr(e, 'data') and e.data:
                error_msg = f"GitHub API error: {e.data.get('message', str(e))}"
            else:
                error_msg = f"GitHub API error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            if "rate limit" in str(e).lower():
                error_msg = "GitHub API rate limit exceeded. Please try again later."
            elif "403" in str(e):
                error_msg = "Access forbidden. Please check your token permissions."
            elif "404" in str(e):
                error_msg = "Resource not found. Please check your token and permissions."
            else:
                error_msg = f"Error fetching repositories: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def create_repository(self, name, description="", private=False):
        """Create a new repository"""
        try:
            logger.info(f"Creating repository: {name}")
            
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True
            )
            
            logger.info(f"Successfully created repository: {repo.full_name}")
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'clone_url': repo.clone_url,
                'html_url': repo.html_url
            }
            
        except GithubException as e:
            error_msg = f"Failed to create repository: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating repository: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_repository_contents(self, repo_name, path=""):
        """Get repository contents"""
        try:
            repo = self.github_client.get_repo(repo_name)
            contents = repo.get_contents(path)
            
            if isinstance(contents, list):
                return [{'name': item.name, 'type': item.type, 'path': item.path} for item in contents]
            else:
                return [{'name': contents.name, 'type': contents.type, 'path': contents.path}]
                
        except Exception as e:
            logger.error(f"Error getting repository contents: {str(e)}")
            raise Exception(f"Error getting repository contents: {str(e)}")
    
    def search_repositories(self, query, repo_list):
        """Search repositories by name or description"""
        try:
            if not query:
                return repo_list
            
            query = query.lower()
            filtered_repos = []
            
            for repo in repo_list:
                if (query in repo['name'].lower() or 
                    query in repo['description'].lower() or
                    (repo['language'] and query in repo['language'].lower())):
                    filtered_repos.append(repo)
            
            logger.info(f"Search '{query}' returned {len(filtered_repos)} results")
            return filtered_repos
            
        except Exception as e:
            logger.error(f"Error searching repositories: {str(e)}")
            return repo_list