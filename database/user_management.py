from typing import List, Dict, Any, Tuple
from .db_connection import get_db_connection

def get_all_users() -> List[Dict[str, Any]]:
    """
    Get a list of all users in the system
    """
    conn = get_db_connection()
    users = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, is_admin, created_at FROM users ORDER BY id")
            
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            
            for row in rows:
                user_dict = dict(zip(column_names, row))
                # Convert datetime to string for JSON serialization
                if 'created_at' in user_dict and user_dict['created_at']:
                    user_dict['created_at'] = user_dict['created_at'].isoformat()
                users.append(user_dict)
            
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching users: {e}")
            if conn:
                conn.close()
    
    return users

def delete_user(user_id: int) -> Tuple[bool, str]:
    """
    Delete a user from the system
    """
    conn = get_db_connection()
    if conn:
        try:
            # Check if user is the last admin
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
            admin_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return False, "User not found"
            
            is_admin = user[0]
            
            if is_admin and admin_count <= 1:
                cursor.close()
                conn.close()
                return False, "Cannot delete the last admin user"
            
            # Delete the user
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True, "User deleted successfully"
            
        except Exception as e:
            conn.close()
            return False, f"Error deleting user: {str(e)}"
    
    return False, "Database connection error"

def update_user_admin_status(user_id: int, is_admin: bool) -> Tuple[bool, str]:
    """
    Update a user's admin status
    """
    conn = get_db_connection()
    if conn:
        try:
            # Check if user is the last admin and we're trying to remove admin privileges
            cursor = conn.cursor()
            
            if not is_admin:
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
                admin_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    cursor.close()
                    conn.close()
                    return False, "User not found"
                
                current_is_admin = user[0]
                
                if current_is_admin and admin_count <= 1:
                    cursor.close()
                    conn.close()
                    return False, "Cannot remove admin privileges from the last admin user"
            
            # Update the user
            cursor.execute("UPDATE users SET is_admin = %s WHERE id = %s", (is_admin, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            status = "granted" if is_admin else "revoked"
            return True, f"Admin privileges {status} successfully"
            
        except Exception as e:
            conn.close()
            return False, f"Error updating user: {str(e)}"
    
    return False, "Database connection error"