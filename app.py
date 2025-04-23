import os
import streamlit as st
from datetime import datetime
from database.user_auth import authenticate_user, register_user, create_user_table, create_initial_admin
from database.user_management import get_all_users, delete_user, update_user_admin_status
from models.document_processor import DocumentProcessor
from models.chatbot import ComplianceChatbot
from utils.helpers import format_timestamp, validate_pdf, display_pdf_preview, create_necessary_directories, SessionLogger

# Page configuration
st.set_page_config(
    page_title="Compliance Assistant",
    page_icon="📚",
    layout="wide",
)

# Initialize document processor and chatbot
@st.cache_resource
def initialize_components():
    # Create necessary directories
    create_necessary_directories()
    
    # Initialize document processor and chatbot
    doc_processor = DocumentProcessor(data_dir="data")
    chatbot = ComplianceChatbot(document_processor=doc_processor)
    return doc_processor, chatbot

# Initialize user table
def initialize_database():
    create_user_table()
    create_initial_admin()

# Main application
def main():
    # Initialize components
    doc_processor, chatbot = initialize_components()
    initialize_database()
    
    # Session state initialization
    if "user" not in st.session_state:
        st.session_state.user = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "login"
    
    # Sidebar
    with st.sidebar:
        st.title("📚 Compliance Assistant")
        
        if st.session_state.user:
            st.success(f"Logged in as: {st.session_state.user['username']}")
            if st.session_state.user.get("is_admin", False):
                st.info("Admin Role")
            
            # Logout button
            if st.button("Logout"):
                st.session_state.user = None
                st.session_state.current_tab = "login"
                st.rerun()
        
        # Navigation
        if st.session_state.user:
            st.divider()
            st.subheader("Navigation")
            
            if st.button("Chat Interface", key="nav_chat"):
                st.session_state.current_tab = "chat"
                st.rerun()
            
            # Document management (admin only)
            if st.session_state.user and st.session_state.user.get("is_admin", False):
                if st.button("Document Management", key="nav_docs"):
                    st.session_state.current_tab = "documents"
                    st.rerun()
                
                if st.button("User Management", key="nav_users"):
                    st.session_state.current_tab = "users"
                    st.rerun()
    
    # Main content area - tabs
    if st.session_state.current_tab == "login":
        render_login_page()
    elif st.session_state.current_tab == "chat":
        render_chat_interface(chatbot, doc_processor)
    elif st.session_state.current_tab == "documents" and st.session_state.user and st.session_state.user.get("is_admin", False):
        render_document_management(doc_processor)
    elif st.session_state.current_tab == "users" and st.session_state.user and st.session_state.user.get("is_admin", False):
        render_user_management()
    else:
        # Default to login if user not logged in, otherwise chat
        if st.session_state.user:
            render_chat_interface(chatbot, doc_processor)
            st.session_state.current_tab = "chat"
        else:
            render_login_page()
            st.session_state.current_tab = "login"

def render_login_page():
    st.title("Login to Compliance Assistant")
    
    # Create tabs for login and register
    login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        with st.form(key="login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button(label="Login")
            
            if submit_button:
                if username and password:
                    success, user_data, message = authenticate_user(username, password)
                    if success:
                        st.session_state.user = user_data
                        st.session_state.current_tab = "chat"
                        st.success(message)
                        # Log the login activity
                        SessionLogger.log_activity(user_data["id"], "login")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both username and password")
    
    with register_tab:
        with st.form(key="register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_button = st.form_submit_button(label="Register")
            
            if submit_button:
                if new_username and new_password:
                    if new_password == confirm_password:
                        success, message = register_user(new_username, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")

def render_chat_interface(chatbot, doc_processor):
    st.title("Chat with Compliance Assistant")
    
    # Check if there are any documents in the system
    documents = doc_processor.get_all_documents()
    if not documents:
        st.warning("There are no compliance documents uploaded yet. Please ask an administrator to upload documents.")
        return
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("View Sources"):
                    for source in message["sources"]:
                        st.markdown(f"- **{source['source']}** (Relevance Score: {source['score']:.2f})")
    
    # Input for new message
    if user_input := st.chat_input("Ask a question about compliance..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = chatbot.generate_response(user_input)
                st.markdown(response)
                
                if sources:
                    with st.expander("View Sources"):
                        for source in sources:
                            st.markdown(f"- **{source['source']}** (Relevance Score: {source['score']:.2f})")
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "sources": sources
        })
        
        # Log the chat activity
        if st.session_state.user:
            SessionLogger.log_activity(st.session_state.user["id"], "chat", f"Query: {user_input[:50]}...")
    
    # Clear chat button
    if st.button("Clear Chat", key="clear_chat"):
        st.session_state.messages = []
        chatbot.reset_chat_history()
        st.rerun()
def render_document_management(doc_processor):
    st.title("Document Management")
    st.write("Upload and manage compliance documents here.")
    
    # Upload new documents
    with st.form("upload_form"):
        uploaded_files = st.file_uploader(
            "Upload PDF files", type="pdf", accept_multiple_files=True
        )
        submit_button = st.form_submit_button("Upload Documents")
        
        if submit_button and uploaded_files:
            successes = []
            failures = []
            for uploaded_file in uploaded_files:
                filename = uploaded_file.name
                if validate_pdf(uploaded_file):
                    with st.spinner(f"Processing {filename}..."):
                        success = doc_processor.process_pdf(uploaded_file, filename)
                    if success:
                        successes.append(filename)
                        if st.session_state.user:
                            SessionLogger.log_activity(
                                st.session_state.user["id"], 
                                "upload_document", 
                                f"File: {filename}"
                            )
                    else:
                        failures.append(filename)
                else:
                    failures.append(filename)
            
            if successes:
                st.success(f"Successfully uploaded and processed: {', '.join(successes)}")
            if failures:
                st.error(f"Failed to process: {', '.join(failures)}")
            
            st.rerun()
    
    # Document list (unchanged)
    st.subheader("Uploaded Documents")
    documents = doc_processor.get_all_documents()
    
    if not documents:
        st.info("No documents have been uploaded yet.")
    else:
        for doc_id, doc_info in documents.items():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{doc_info['filename']}**")
                with col2:
                    upload_time = datetime.fromisoformat(doc_info['uploaded_at'])
                    st.write(f"Uploaded: {format_timestamp(doc_info['uploaded_at'])}")
                with col3:
                    if st.button("Delete", key=f"delete_{doc_id}"):
                        if doc_processor.delete_document(doc_id):
                            st.success("Document deleted successfully!")
                            if st.session_state.user:
                                SessionLogger.log_activity(
                                    st.session_state.user["id"], 
                                    "delete_document", 
                                    f"File: {doc_info['filename']}"
                                )
                            st.rerun()
                        else:
                            st.error("Failed to delete document.")
                
                st.write(f"Chunks: {doc_info['chunk_count']}")
                st.divider()
                
def render_user_management():
    st.title("User Management")
    st.write("Manage system users.")
    
    # Create new user section
    with st.form("create_user_form"):
        st.subheader("Create New User")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        is_admin = st.checkbox("Admin Privileges")
        submit_button = st.form_submit_button("Create User")
        
        if submit_button:
            if username and password:
                success, message = register_user(username, password, is_admin)
                if success:
                    st.success(message)
                    # Log the user creation
                    if st.session_state.user:
                        SessionLogger.log_activity(st.session_state.user["id"], "create_user", f"Username: {username}, Admin: {is_admin}")
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields")
    
    # User list section
    st.subheader("User List")
    users = get_all_users()
    
    if not users:
        st.info("No users found.")
    else:
        # Create a table for users
        for user in users:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{user['username']}**")
                    st.caption(f"ID: {user['id']}")
                
                with col2:
                    role = "Admin" if user['is_admin'] else "User"
                    st.write(f"Role: {role}")
                
                with col3:
                    created_at = format_timestamp(user['created_at'])
                    st.write(f"Created: {created_at}")
                
                with col4:
                    # Don't allow actions on your own account
                    if st.session_state.user and user['id'] != st.session_state.user['id']:
                        # Toggle admin status
                        admin_action = "Remove Admin" if user['is_admin'] else "Make Admin"
                        if st.button(admin_action, key=f"admin_{user['id']}"):
                            success, message = update_user_admin_status(user['id'], not user['is_admin'])
                            if success:
                                st.success(message)
                                # Log the role change
                                if st.session_state.user:
                                    SessionLogger.log_activity(st.session_state.user["id"], "update_user_role", f"User: {user['username']}, New Role: {'Regular' if user['is_admin'] else 'Admin'}")
                                st.rerun()
                            else:
                                st.error(message)
                        
                        # Delete user
                        if st.button("Delete", key=f"delete_user_{user['id']}"):
                            success, message = delete_user(user['id'])
                            if success:
                                st.success(message)
                                # Log the user deletion
                                if st.session_state.user:
                                    SessionLogger.log_activity(st.session_state.user["id"], "delete_user", f"Username: {user['username']}")
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.write("Current User")
            
            st.divider()

# Run the app
if __name__ == "__main__":
    main()