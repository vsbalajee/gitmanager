import streamlit as st
import os
from utils.auth import GitHubAuth, init_session_state
from utils.logger import logger

# Page configuration
st.set_page_config(
    page_title="GitHub Repository Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
init_session_state()

def main():
    """Main application function"""
    try:
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin: 1rem 0;
        }
        .auth-form {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Check if user is authenticated
        if st.session_state.authenticated:
            show_dashboard()
        else:
            show_landing_page()
    
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application error: {str(e)}")

def show_landing_page():
    """Display the landing page with authentication"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 GitHub Repository Manager</h1>
        <h3>Developer's Command Center for Repository Operations</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    st.markdown("""
    Welcome to your personal GitHub repository management hub! This tool is designed specifically 
    for developers who need quick and efficient access to their GitHub repositories.
    """)
    
    # Features section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📥 Repository Download</h4>
            <ul>
                <li>Browse all your GitHub repositories in one place</li>
                <li>One-click repository cloning to your local machine</li>
                <li>Choose your preferred download location</li>
                <li>Automatic folder organization</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📤 Local to GitHub Upload</h4>
            <ul>
                <li>Upload any local project folder directly to GitHub</li>
                <li>Create new repositories on-the-fly</li>
                <li>Automatic git initialization and first commit</li>
                <li>Seamless integration with your GitHub account</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Security features
    st.markdown("""
    <div class="feature-card">
        <h4>🔐 Secure Access</h4>
        <ul>
            <li>Personal Access Token (PAT) authentication</li>
            <li>Session-based security</li>
            <li>No credentials stored locally</li>
            <li>Comprehensive error handling and logging</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication form
    st.markdown("---")
    st.subheader("🔑 Get Started")
    
    with st.container():
        st.markdown('<div class="auth-form">', unsafe_allow_html=True)
        
        # Instructions
        with st.expander("📋 How to get your GitHub Personal Access Token", expanded=False):
            st.markdown("""
            1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
            2. Click "Generate new token" (classic)
            3. Give it a descriptive name
            4. Select the following scopes:
               - `repo` (Full control of private repositories)
               - `user` (Read user profile data)
            5. Click "Generate token"
            6. Copy the token immediately (you won't see it again!)
            """)
        
        # Authentication form
        with st.form("auth_form"):
            st.markdown("#### Enter Your Details")
            
            col1, col2 = st.columns(2)
            with col1:
                developer_name = st.text_input(
                    "Developer Name:",
                    placeholder="Your Name",
                    help="This is just for display purposes"
                )
            
            with col2:
                github_token = st.text_input(
                    "GitHub Personal Access Token:",
                    type="password",
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
                    help="Your GitHub PAT with repo access"
                )
            
            # Try to get default token from secrets
            if not github_token:
                try:
                    default_token = st.secrets.get("github", {}).get("default_pat", "")
                    if default_token and default_token != "your_github_pat_here":
                        st.info("Using default token from configuration")
                        github_token = default_token
                except:
                    pass
            
            submitted = st.form_submit_button("🚀 Connect to GitHub", use_container_width=True)
            
            if submitted:
                authenticate_user(developer_name, github_token)
        
        st.markdown('</div>', unsafe_allow_html=True)

def authenticate_user(developer_name, github_token):
    """Authenticate user with GitHub"""
    try:
        if not developer_name:
            st.error("Please enter your developer name.")
            return
        
        if not github_token:
            st.error("Please enter your GitHub Personal Access Token.")
            return
        
        # Show authentication progress
        with st.spinner("Authenticating with GitHub..."):
            success, message = st.session_state.github_auth.authenticate(github_token)
        
        if success:
            # Get user info
            user_info = st.session_state.github_auth.get_user_info()
            
            if user_info:
                # Update session state
                st.session_state.authenticated = True
                st.session_state.developer_name = developer_name
                st.session_state.github_token = github_token
                st.session_state.user_info = user_info
                
                st.success(f"✅ {message}")
                logger.info(f"User authenticated: {user_info['login']}")
                
                # Rerun to show dashboard
                st.rerun()
            else:
                st.error("Failed to retrieve user information.")
        else:
            st.error(f"❌ {message}")
            logger.warning(f"Authentication failed: {message}")
    
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        logger.error(f"Authentication error: {str(e)}")

def show_dashboard():
    """Display the main dashboard for authenticated users"""
    
    # Sidebar user info
    with st.sidebar:
        st.markdown("### 👤 User Information")
        
        user_info = st.session_state.user_info
        if user_info:
            if user_info.get('avatar_url'):
                st.image(user_info['avatar_url'], width=100)
            
            st.markdown(f"**Name:** {st.session_state.developer_name}")
            st.markdown(f"**GitHub:** {user_info['login']}")
            st.markdown(f"**Public Repos:** {user_info['public_repos']}")
            st.markdown(f"**Private Repos:** {user_info['private_repos']}")
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()

    # Main dashboard
    st.title(f"Welcome back, {st.session_state.developer_name}! 👋")
    
    # Quick stats
    user_info = st.session_state.user_info
    if user_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Public Repositories", user_info['public_repos'])
        with col2:
            st.metric("Private Repositories", user_info['private_repos'])
        with col3:
            total_repos = user_info['public_repos'] + user_info['private_repos']
            st.metric("Total Repositories", total_repos)
    
    st.markdown("---")
    
    # Navigation cards
    st.subheader("🎯 What would you like to do?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📁 Browse & Download Repositories</h4>
            <p>View all your repositories, search, filter, and download them to your local machine.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 Browse Repositories", use_container_width=True):
            st.switch_page("pages/01_Repository_List.py")
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📤 Upload Projects</h4>
            <p>Upload local projects or files to create new GitHub repositories.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📤 Upload Project", use_container_width=True):
            st.switch_page("pages/02_Upload_Project.py")
    
    # Recent activity or tips
    st.markdown("---")
    st.subheader("💡 Tips")
    
    tips = [
        "🔍 Use the search function to quickly find specific repositories",
        "📁 You can customize the default download location in the configuration",
        "🔒 Private repositories are marked with a lock icon",
        "📊 Repository statistics help you understand your project portfolio",
        "🚀 Bulk operations are available for managing multiple repositories"
    ]
    
    for tip in tips:
        st.markdown(f"- {tip}")

def logout_user():
    """Logout user and clear session state"""
    try:
        logger.info(f"User logged out: {st.session_state.get('user_info', {}).get('login', 'Unknown')}")
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinitialize
        init_session_state()
        
        st.rerun()
    
    except Exception as e:
        st.error(f"Logout error: {str(e)}")
        logger.error(f"Logout error: {str(e)}")

if __name__ == "__main__":
    main()