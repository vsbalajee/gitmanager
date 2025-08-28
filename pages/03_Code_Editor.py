import streamlit as st
import os
from pathlib import Path
from utils.github_manager import GitHubManager
from utils.git_operations import GitOperations
from utils.logger import logger
from utils.auth import init_session_state
import git
from datetime import datetime

# Initialize session state
init_session_state()

def main():
    st.set_page_config(
        page_title="Code Editor",
        page_icon="💻",
        layout="wide"
    )
    
    st.title("💻 Code Editor")
    
    # Check authentication
    if not st.session_state.authenticated:
        st.error("Please authenticate first from the main page.")
        st.stop()
    
    try:
        # Initialize managers
        github_manager = GitHubManager(st.session_state.github_auth.get_github_client())
        git_ops = GitOperations()
        
        st.markdown("""
        ### 🔧 Edit Your Repository Code
        
        This tool allows you to:
        1. Browse your local repositories
        2. Edit files directly in the browser
        3. Commit and push changes back to GitHub
        """)
        
        # Step 1: Select local repository
        local_repo_path = select_local_repository()
        
        if local_repo_path:
            # Step 2: Browse and edit files
            edit_repository_files(local_repo_path, git_ops)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error in code editor: {str(e)}")

def select_local_repository():
    """Select a local repository to edit"""
    st.subheader("📁 Select Repository to Edit")
    
    # Get default download path
    try:
        default_path = st.secrets.get("github", {}).get("default_clone_path", "C:/Users/BALAJI/Downloads")
    except:
        default_path = "C:/Users/BALAJI/Downloads"
    
    # Input for repository path
    repo_path = st.text_input(
        "Repository Path:",
        value=default_path,
        help="Enter the path to your local repository"
    )
    
    if repo_path and os.path.exists(repo_path):
        # List directories that contain .git folders
        git_repos = []
        try:
            for item in os.listdir(repo_path):
                item_path = os.path.join(repo_path, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '.git')):
                    git_repos.append(item)
        except Exception as e:
            st.error(f"Error reading directory: {str(e)}")
            return None
        
        if git_repos:
            selected_repo = st.selectbox(
                "Select Repository:",
                git_repos,
                help="Choose a repository to edit"
            )
            
            if selected_repo:
                full_repo_path = os.path.join(repo_path, selected_repo)
                st.success(f"Selected: {full_repo_path}")
                return full_repo_path
        else:
            st.warning("No Git repositories found in the specified path.")
    
    return None

def edit_repository_files(repo_path, git_ops):
    """Edit files in the selected repository"""
    st.subheader(f"📝 Editing: {os.path.basename(repo_path)}")
    
    # Get repository status
    try:
        repo = git.Repo(repo_path)
        current_branch = repo.active_branch.name
        st.info(f"Current branch: **{current_branch}**")
    except Exception as e:
        st.error(f"Error accessing repository: {str(e)}")
        return
    
    # File browser
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 📂 File Browser")
        selected_file = browse_files(repo_path)
    
    with col2:
        if selected_file:
            st.markdown(f"#### ✏️ Editing: {os.path.basename(selected_file)}")
            edit_file(selected_file, repo_path, git_ops)

def browse_files(repo_path, current_path=""):
    """Browse files in the repository"""
    full_path = os.path.join(repo_path, current_path) if current_path else repo_path
    
    try:
        items = []
        
        # Add parent directory option if not at root
        if current_path:
            parent_path = os.path.dirname(current_path)
            items.append(("📁 ..", parent_path, True))
        
        # List directories and files
        for item in sorted(os.listdir(full_path)):
            if item.startswith('.git'):
                continue
                
            item_path = os.path.join(full_path, item)
            relative_path = os.path.join(current_path, item) if current_path else item
            
            if os.path.isdir(item_path):
                items.append((f"📁 {item}", relative_path, True))
            else:
                # Only show text files
                if is_text_file(item):
                    items.append((f"📄 {item}", relative_path, False))
        
        # Create clickable file list
        for display_name, path, is_dir in items:
            if st.button(display_name, key=f"file_{path}"):
                if is_dir:
                    if display_name == "📁 ..":
                        st.session_state.current_path = path
                    else:
                        st.session_state.current_path = path
                    st.rerun()
                else:
                    return os.path.join(repo_path, path)
        
        # Handle current path from session state
        if hasattr(st.session_state, 'current_path'):
            return browse_files(repo_path, st.session_state.current_path)
            
    except Exception as e:
        st.error(f"Error browsing files: {str(e)}")
    
    return None

def is_text_file(filename):
    """Check if file is likely a text file"""
    text_extensions = {
        '.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml',
        '.md', '.txt', '.csv', '.sql', '.sh', '.bat', '.ps1', '.php',
        '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.rb', '.swift',
        '.kt', '.scala', '.r', '.m', '.pl', '.lua', '.vim', '.ini', '.cfg',
        '.conf', '.log', '.gitignore', '.dockerfile', '.makefile'
    }
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in text_extensions or filename.lower() in ['readme', 'license', 'makefile', 'dockerfile']

def edit_file(file_path, repo_path, git_ops):
    """Edit a specific file"""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # File info
        file_size = os.path.getsize(file_path)
        st.caption(f"File size: {file_size} bytes")
        
        # Code editor
        edited_content = st.text_area(
            "File Content:",
            value=content,
            height=400,
            help="Edit the file content here"
        )
        
        # Save and commit options
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save File", use_container_width=True):
                save_file(file_path, edited_content)
        
        with col2:
            if st.button("🚀 Save & Commit", use_container_width=True):
                save_and_commit(file_path, edited_content, repo_path, git_ops)
        
        # Show file changes
        if content != edited_content:
            st.warning("⚠️ File has unsaved changes")
            
            with st.expander("📋 View Changes"):
                st.markdown("**Original:**")
                st.code(content[:500] + "..." if len(content) > 500 else content)
                st.markdown("**Modified:**")
                st.code(edited_content[:500] + "..." if len(edited_content) > 500 else edited_content)
    
    except Exception as e:
        st.error(f"Error editing file: {str(e)}")

def save_file(file_path, content):
    """Save file content"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        st.success(f"✅ File saved: {os.path.basename(file_path)}")
        logger.info(f"File saved: {file_path}")
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        logger.error(f"Error saving file {file_path}: {str(e)}")

def save_and_commit(file_path, content, repo_path, git_ops):
    """Save file and commit changes"""
    try:
        # Save file first
        save_file(file_path, content)
        
        # Commit changes
        repo = git.Repo(repo_path)
        
        # Add file to staging
        relative_path = os.path.relpath(file_path, repo_path)
        repo.git.add(relative_path)
        
        # Check if there are changes to commit
        if repo.is_dirty():
            # Get commit message
            commit_msg = st.text_input(
                "Commit Message:",
                value=f"Update {os.path.basename(file_path)}",
                key="commit_message"
            )
            
            if st.button("✅ Commit Changes"):
                # Commit
                repo.index.commit(commit_msg)
                
                # Push to remote
                if st.checkbox("Push to GitHub", value=True):
                    try:
                        origin = repo.remote('origin')
                        origin.push()
                        st.success("🎉 Changes committed and pushed to GitHub!")
                        logger.info(f"Changes committed and pushed for {file_path}")
                    except Exception as e:
                        st.error(f"Commit successful but push failed: {str(e)}")
                        logger.error(f"Push failed for {file_path}: {str(e)}")
                else:
                    st.success("✅ Changes committed locally!")
                    logger.info(f"Changes committed locally for {file_path}")
        else:
            st.info("No changes to commit.")
    
    except Exception as e:
        st.error(f"Error committing changes: {str(e)}")
        logger.error(f"Error committing changes for {file_path}: {str(e)}")

if __name__ == "__main__":
    main()