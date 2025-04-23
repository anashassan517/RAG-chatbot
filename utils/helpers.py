import os
import time
from datetime import datetime
import streamlit as st

def format_timestamp(timestamp_str):
    """Format timestamp string to a readable date/time format"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%b %d, %Y - %I:%M %p")
    except:
        return timestamp_str

def create_necessary_directories():
    """Create necessary directories for the application if they don't exist"""
    dirs = [
        "data",
        "data/pdfs",
        "data/vector_store"
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    return True

def validate_pdf(file):
    """Validate if a file is a PDF"""
    if file is None:
        return False
    
    # Check file type
    if not file.name.lower().endswith('.pdf'):
        return False
    
    # Check file size (limit to 20MB)
    if file.size > 20 * 1024 * 1024:  # 20MB in bytes
        return False
    
    return True

def display_pdf_preview(pdf_file):
    """Display a preview of the PDF file"""
    try:
        # Save to a temporary file
        with open("temp_pdf.pdf", "wb") as f:
            f.write(pdf_file.read())
        
        # Reset pointer
        pdf_file.seek(0)
        
        # Display PDF using iframe
        with st.expander("PDF Preview"):
            st.write(f"File: {pdf_file.name}, Size: {pdf_file.size / 1024:.1f} KB")
            st.markdown(
                f'<iframe src="temp_pdf.pdf" width="100%" height="500"></iframe>',
                unsafe_allow_html=True
            )
            
        # Remove temporary file
        os.remove("temp_pdf.pdf")
    except Exception as e:
        st.error(f"Error previewing PDF: {str(e)}")

class SessionLogger:
    """Class to log user session activities"""
    
    @staticmethod
    def log_activity(user_id, activity_type, details=""):
        """Log a user activity"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | User {user_id} | {activity_type} | {details}\n"
        
        try:
            os.makedirs("logs", exist_ok=True)
            log_file = os.path.join("logs", f"activity_{datetime.now().strftime('%Y%m%d')}.log")
            
            with open(log_file, "a") as f:
                f.write(log_entry)
                
            return True
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False