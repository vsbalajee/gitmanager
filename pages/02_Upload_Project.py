import streamlit as st
import os
from pathlib import Path
from utils.github_manager import GitHubManager
from utils.git_operations import GitOperations
from utils.logger import logger
from utils.auth import init_session_state
import tempfile
import shutil

# Initialize session state
init_session_state()

def main():
    st.set_page_config(
        page_title="Upload Project",
        page_icon="📤",
        layout="wide"
    )
    
    st.title("📤 Upload Project to GitHub")
    
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
        
        st.markdown("""
        ### 🚀 Upload Your Local Project to GitHub
        
        This tool helps you upload a local project folder to GitHub by:
        1. Creating a new repository on GitHub
        2. Initializing git in your local folder
        3. Pushing your code to the new repository
        """)
        
        # Upload method selection
        upload_method = st.radio(
            "Choose upload method:",
            ["📁 Select Local Folder", "📋 Upload Files"],
            index=0
        )
        
        if upload_method == "📁 Select Local Folder":
            handle_folder_upload(github_manager, git_ops)
        else:
            handle_file_upload(github_manager, git_ops)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error in upload project: {str(e)}")

def handle_folder_upload(github_manager, git_ops):
    """Handle folder-based upload"""
    st.subheader("📁 Local Folder Upload")
    
    # Project details form
    with st.form("folder_upload_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            local_path = st.text_input(
                "Local Project Path:",
                placeholder="/path/to/your/project",
                help="Enter the full path to your local project folder"
            )
            
            repo_name = st.text_input(
                "Repository Name:",
                placeholder="my-awesome-project",
                help="Name for the new GitHub repository"
            )
        
        with col2:
            repo_description = st.text_area(
                "Repository Description:",
                placeholder="A brief description of your project",
                height=100
            )
            
            is_private = st.checkbox("Make repository private", value=False)
        
        commit_message = st.text_input(
            "Initial Commit Message:",
            value="Initial commit",
            help="Message for the first commit"
        )
        
        submitted = st.form_submit_button("🚀 Create Repository & Upload")
        
        if submitted:
            upload_folder_to_github(
                local_path, repo_name, repo_description, 
                is_private, commit_message, github_manager, git_ops
            )

def handle_file_upload(github_manager, git_ops):
    """Handle file-based upload"""
    st.subheader("📋 File Upload")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        help="Select multiple files to upload to a new repository"
    )
    
    if uploaded_files:
        st.success(f"Selected {len(uploaded_files)} files")
        
        # Show file list
        with st.expander("📄 Selected Files"):
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size} bytes)")
        
        # Repository details
        with st.form("file_upload_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                repo_name = st.text_input(
                    "Repository Name:",
                    placeholder="my-file-project"
                )
            
            with col2:
                is_private = st.checkbox("Make repository private", value=False)
            
            repo_description = st.text_area(
                "Repository Description:",
                placeholder="Project created from uploaded files"
            )
            
            commit_message = st.text_input(
                "Initial Commit Message:",
                value="Initial commit with uploaded files"
            )
            
            submitted = st.form_submit_button("🚀 Create Repository & Upload Files")
            
            if submitted:
                upload_files_to_github(
                    uploaded_files, repo_name, repo_description,
                    is_private, commit_message, github_manager, git_ops
                )

def upload_folder_to_github(local_path, repo_name, repo_description, is_private, commit_message, github_manager, git_ops):
    """Upload local folder to GitHub"""
    try:
        # Validation
        if not local_path or not repo_name:
            st.error("Please provide both local path and repository name.")
            return
        
        if not os.path.exists(local_path):
            st.error(f"Local path does not exist: {local_path}")
            return
        
        if not os.path.isdir(local_path):
            st.error(f"Path is not a directory: {local_path}")
            return
        
        # Check if directory has files
        if not any(os.scandir(local_path)):
            st.error("Directory is empty. Please select a directory with files.")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Create GitHub repository
        status_text.text("Creating GitHub repository...")
        progress_bar.progress(25)
        
        try:
            repo_info = github_manager.create_repository(
                name=repo_name,
                description=repo_description,
                private=is_private
            )
        except Exception as e:
            st.error(f"Failed to create repository: {str(e)}")
            return
        
        # Step 2: Initialize and push
        status_text.text("Initializing git and pushing files...")
        progress_bar.progress(50)
        
        try:
            success = git_ops.initialize_and_push(
                local_path,
                repo_info['clone_url'],
                commit_message
            )
            
            if success:
                progress_bar.progress(100)
                status_text.text("Upload completed successfully!")
                
                st.success("🎉 Project uploaded successfully!")
                
                # Show repository info
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Repository:** {repo_info['full_name']}")
                    st.info(f"**URL:** {repo_info['html_url']}")
                with col2:
                    dir_size = git_ops.get_directory_size(local_path)
                    st.info(f"**Size:** {dir_size / (1024*1024):.2f} MB")
                    st.info(f"**Privacy:** {'Private' if is_private else 'Public'}")
                
                st.markdown(f"[🌐 View Repository]({repo_info['html_url']})")
                
                logger.info(f"Successfully uploaded {local_path} to {repo_info['full_name']}")
            else:
                st.warning("No files were committed (directory might be empty or contain only ignored files).")
        
        except Exception as e:
            st.error(f"Failed to push to repository: {str(e)}")
            logger.error(f"Failed to push {local_path} to {repo_info['full_name']}: {str(e)}")
        
        finally:
            progress_bar.empty()
            status_text.empty()
    
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        logger.error(f"Upload failed for {local_path}: {str(e)}")

def upload_files_to_github(uploaded_files, repo_name, repo_description, is_private, commit_message, github_manager, git_ops):
    """Upload files to GitHub"""
    try:
        if not repo_name:
            st.error("Please provide a repository name.")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        git_ops.temp_dirs.append(temp_dir)
        
        try:
            # Step 1: Save uploaded files
            status_text.text("Saving uploaded files...")
            progress_bar.progress(20)
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            # Step 2: Create GitHub repository
            status_text.text("Creating GitHub repository...")
            progress_bar.progress(40)
            
            repo_info = github_manager.create_repository(
                name=repo_name,
                description=repo_description,
                private=is_private
            )
            
            # Step 3: Initialize and push
            status_text.text("Pushing files to repository...")
            progress_bar.progress(70)
            
            success = git_ops.initialize_and_push(
                temp_dir,
                repo_info['clone_url'],
                commit_message
            )
            
            if success:
                progress_bar.progress(100)
                status_text.text("Upload completed successfully!")
                
                st.success("🎉 Files uploaded successfully!")
                
                # Show repository info
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Repository:** {repo_info['full_name']}")
                    st.info(f"**Files:** {len(uploaded_files)}")
                with col2:
                    total_size = sum(file.size for file in uploaded_files)
                    st.info(f"**Size:** {total_size / 1024:.2f} KB")
                    st.info(f"**Privacy:** {'Private' if is_private else 'Public'}")
                
                st.markdown(f"[🌐 View Repository]({repo_info['html_url']})")
                
                logger.info(f"Successfully uploaded {len(uploaded_files)} files to {repo_info['full_name']}")
            else:
                st.warning("No files were committed.")
        
        finally:
            # Cleanup
            git_ops.cleanup_temp_dirs()
            progress_bar.empty()
            status_text.empty()
    
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        logger.error(f"File upload failed: {str(e)}")

if __name__ == "__main__":
    main()