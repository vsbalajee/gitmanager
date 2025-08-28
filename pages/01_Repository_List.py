import streamlit as st
import pandas as pd
from utils.github_manager import GitHubManager
from utils.git_operations import GitOperations
from utils.logger import logger
from utils.auth import init_session_state
import os
from datetime import datetime

# Initialize session state
init_session_state()

def main():
    st.set_page_config(
        page_title="Repository List",
        page_icon="📁",
        layout="wide"
    )
    
    st.title("📁 Your GitHub Repositories")
    
    # Check authentication
    if not st.session_state.authenticated:
        st.error("Please authenticate first from the main page.")
        st.stop()
    
    try:
        # Initialize managers
        github_manager = GitHubManager(st.session_state.github_auth.get_github_client())
        git_ops = GitOperations()
        
        # Validate git installation
        git_valid, git_msg = git_ops.validate_git_installation()
        if not git_valid:
            st.error(f"Git installation issue: {git_msg}")
            st.info("Please ensure Git is installed and accessible from command line.")
            return
        
        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        repo_type = st.sidebar.selectbox(
            "Repository Type",
            ["all", "public", "private"],
            index=0
        )
        
        search_query = st.sidebar.text_input("🔎 Search repositories")
        
        # Load repositories
        with st.spinner("Loading repositories..."):
            try:
                # Check if GitHub client is still valid
                if not st.session_state.github_auth.get_github_client():
                    st.error("GitHub authentication expired. Please re-authenticate.")
                    st.stop()
                
                repositories = github_manager.get_repositories(repo_type)
                
                if search_query:
                    repositories = github_manager.search_repositories(search_query, repositories)
                
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower():
                    st.error("⚠️ GitHub API rate limit exceeded. Please wait a few minutes and try again.")
                elif "403" in error_msg or "forbidden" in error_msg.lower():
                    st.error("🔒 Access forbidden. Please check your GitHub token permissions.")
                elif "404" in error_msg:
                    st.error("🔍 Resource not found. Please verify your GitHub token has the correct permissions.")
                else:
                    st.error(f"❌ Error loading repositories: {error_msg}")
                logger.error(f"Error loading repositories: {str(e)}")
                return
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Repositories", len(repositories))
        with col2:
            public_count = sum(1 for repo in repositories if not repo['private'])
            st.metric("Public", public_count)
        with col3:
            private_count = sum(1 for repo in repositories if repo['private'])
            st.metric("Private", private_count)
        with col4:
            total_stars = sum(repo['stars'] for repo in repositories)
            st.metric("Total Stars", total_stars)
        
        if not repositories:
            st.info("No repositories found matching your criteria.")
            return
        
        # Repository cards
        st.subheader(f"📚 Repositories ({len(repositories)})")
        
        # Pagination
        repos_per_page = 10
        total_pages = (len(repositories) - 1) // repos_per_page + 1
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1), index=0)
            start_idx = (page - 1) * repos_per_page
            end_idx = start_idx + repos_per_page
            page_repos = repositories[start_idx:end_idx]
        else:
            page_repos = repositories
        
        # Display repositories
        for repo in page_repos:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Repository header
                    privacy_icon = "🔒" if repo['private'] else "🌐"
                    st.markdown(f"### {privacy_icon} {repo['name']}")
                    
                    # Description
                    st.markdown(f"*{repo['description']}*")
                    
                    # Metadata
                    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
                    with col_meta1:
                        if repo['language']:
                            st.markdown(f"**Language:** {repo['language']}")
                    with col_meta2:
                        st.markdown(f"**⭐ Stars:** {repo['stars']}")
                    with col_meta3:
                        st.markdown(f"**🍴 Forks:** {repo['forks']}")
                    with col_meta4:
                        updated = repo['updated_at'].strftime("%Y-%m-%d")
                        st.markdown(f"**Updated:** {updated}")
                
                with col2:
                    # Action buttons
                    st.markdown("**Actions:**")
                    
                    # View on GitHub
                    st.markdown(f"[🌐 View on GitHub]({repo['html_url']})")
                    
                    # Download button
                    if st.button(f"📥 Download", key=f"download_{repo['name']}", help="Click to download this repository"):
                        st.session_state[f"downloading_{repo['name']}"] = True
                    
                    # Handle download if button was clicked
                    if st.session_state.get(f"downloading_{repo['name']}", False):
                        download_repository(repo, git_ops)
                        # Reset the download state
                        st.session_state[f"downloading_{repo['name']}"] = False
                
                st.divider()
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error in repository list: {str(e)}")

def download_repository(repo, git_ops):
    """Handle repository download"""
    try:
        st.write("---")
        st.subheader(f"📥 Downloading: {repo['name']}")
        
        # Get download path from secrets or use default
        try:
            default_path = st.secrets.get("github", {}).get("default_clone_path", "./downloads")
        except Exception as e:
            logger.warning(f"Could not read default path from secrets: {str(e)}")
            default_path = "./downloads"
        
        # Create form for download configuration
        with st.form(key=f"download_form_{repo['name']}"):
            download_path = st.text_input(
                "Download Location:",
                value=default_path,
                help="Enter the full path where you want to download the repository"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                confirm_download = st.form_submit_button("✅ Start Download", use_container_width=True)
            with col2:
                cancel_download = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if cancel_download:
            st.info("Download cancelled.")
            return
            
        if confirm_download:
            if not download_path.strip():
                st.error("Please enter a valid download path.")
                return
                
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(percentage, message):
                progress_bar.progress(min(percentage, 100))
                status_text.text(message)
            
            try:
                # Validate download path
                download_path = download_path.strip()
                if not os.path.exists(os.path.dirname(download_path)) and download_path != "./downloads":
                    try:
                        os.makedirs(os.path.dirname(download_path), exist_ok=True)
                    except Exception as e:
                        st.error(f"Cannot create download directory: {str(e)}")
                        return
                
                update_progress(10, "Preparing download...")
                
                # Clone repository
                local_path = git_ops.clone_repository(
                    repo['clone_url'],
                    download_path,
                    repo['name'],
                    progress_callback=update_progress
                )
                
                st.success(f"✅ Repository downloaded successfully to: {local_path}")
                
                # Show directory info
                try:
                    dir_size = git_ops.get_directory_size(local_path)
                    st.info(f"📁 Directory size: {dir_size / (1024*1024):.2f} MB")
                except Exception as e:
                    logger.warning(f"Could not calculate directory size: {str(e)}")
                    st.info("📁 Repository downloaded successfully")
                
                logger.info(f"Repository {repo['name']} downloaded to {local_path}")
                
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    st.error(f"❌ Download failed: Directory already exists. Please choose a different location or delete the existing directory.")
                elif "permission" in error_msg.lower():
                    st.error(f"❌ Download failed: Permission denied. Please check folder permissions or choose a different location.")
                elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
                    st.error(f"❌ Download failed: Network error. Please check your internet connection and try again.")
                else:
                    st.error(f"❌ Download failed: {error_msg}")
                logger.error(f"Download failed for {repo['name']}: {str(e)}")
            finally:
                progress_bar.empty()
                status_text.empty()
    
    except Exception as e:
        st.error(f"Error setting up download: {str(e)}")
        logger.error(f"Error setting up download for {repo['name']}: {str(e)}")

if __name__ == "__main__":
    main()