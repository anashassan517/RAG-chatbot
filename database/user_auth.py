import hashlib
import uuid
from .db_connection import get_db_connection

def create_user_table():
    """
    Create the users table if it doesn't exist
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL,
                    salt VARCHAR(36) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("Users table created successfully")
        except Exception as e:
            print(f"Error creating users table: {e}")
        finally:
            cursor.close()
            conn.close()

def hash_password(password, salt=None):
    """
    Hash a password with SHA-256 and a random salt
    """
    if salt is None:
        salt = str(uuid.uuid4())
    
    # Combine password and salt, then hash
    hash_obj = hashlib.sha256((password + salt).encode())
    password_hash = hash_obj.hexdigest()
    
    return password_hash, salt

def register_user(username, password, is_admin=False):
    """
    Register a new user
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection error"
        
    try:
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Username already exists"
        
        # Hash the password
        password_hash, salt = hash_password(password)
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (%s, %s, %s, %s)",
            (username, password_hash, salt, is_admin)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "User registered successfully"
    except Exception as e:
        if conn:
            conn.close()
        return False, f"Error: {str(e)}"

def authenticate_user(username, password):
    """
    Authenticate a user
    """
    conn = get_db_connection()
    if not conn:
        return False, None, "Database connection error"
        
    try:
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute("SELECT id, password_hash, salt, is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return False, None, "Invalid username or password"
        
        user_id, stored_hash, salt, is_admin = user
        
        # Verify password
        input_hash, _ = hash_password(password, salt)
        if input_hash == stored_hash:
            return True, {"id": user_id, "username": username, "is_admin": is_admin}, "Login successful"
        else:
            return False, None, "Invalid username or password"
    except Exception as e:
        if conn:
            conn.close()
        return False, None, f"Error: {str(e)}"

# Function to create an initial admin user if none exists
def create_initial_admin():
    """
    Create an initial admin user if no users exist in the database
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Create an admin user with default credentials
                register_user("admin", "admin", is_admin=True)
                print("Initial admin user created")
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error checking for users: {e}")
            if conn:
                conn.close()