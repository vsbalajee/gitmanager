import streamlit as st
from github import Github, GithubException
from utils.logger import logger
import os
from datetime import datetime

class GitHubManager:
    def __init__(self, github_client):
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
            logger.info(f"Fetching repositories of type: {repo_type}")
            
            if repo_type == "public":
                repos = self.user.get_repos(type="public")
            elif repo_type == "private":
                repos = self.user.get_repos(type="private")
            else:
                repos = self.user.get_repos(type="all")
            
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
            error_msg = f"GitHub API error: {e.data.get('message', str(e))}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
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