import psycopg2
from psycopg2.extras import RealDictCursor
import os
from passlib.context import CryptContext

# Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Database connection string from Render
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://coding_challenge_platform_user:lMxyQpBH4d5hRZhVdlpktt23WUOaIYfJ@dpg-d3fvlah5pdvs73c092hg-a.oregon-postgres.render.com/coding_challenge_platform"
)

def get_db_connection():
    """Get database connection"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def create_user(username: str, email: str, password: str):
    """Create new user"""
    print(f"[DEBUG] Creating user: {username}")
    print(f"[DEBUG] Original password length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Truncate password to 72 bytes for bcrypt
        # bcrypt has a 72 byte limit
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            print(f"[DEBUG] Password too long ({len(password_bytes)} bytes), truncating to 72 bytes")
            # Truncate and decode safely
            truncated_bytes = password_bytes[:72]
            # Remove any incomplete UTF-8 sequences at the end
            while truncated_bytes:
                try:
                    password = truncated_bytes.decode('utf-8')
                    break
                except UnicodeDecodeError:
                    truncated_bytes = truncated_bytes[:-1]
            print(f"[DEBUG] Truncated password length: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
        
        print(f"[DEBUG] Hashing password...")
        hashed_password = pwd_context.hash(password)
        print(f"[DEBUG] Password hashed successfully")
        
        cur.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s) RETURNING id",
            (username, email, hashed_password)
        )
        user_id = cur.fetchone()['id']
        conn.commit()
        print(f"[DEBUG] User created successfully with id: {user_id}")
        return {"success": True, "user_id": user_id, "username": username}
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        error_msg = str(e)
        print(f"[DEBUG] IntegrityError: {error_msg}")
        if "username" in error_msg:
            return {"success": False, "error": "Username already exists"}
        elif "email" in error_msg:
            return {"success": False, "error": "Email already exists"}
        else:
            return {"success": False, "error": "Username or email already exists"}
            
    except Exception as e:
        conn.rollback()
        print(f"[DEBUG] Exception during user creation: {type(e).__name__}: {str(e)}")
        return {"success": False, "error": f"Error: {str(e)}"}
        
    finally:
        cur.close()
        conn.close()

def verify_user(username: str, password: str):
    """Verify user credentials"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        
        # Truncate password to 72 bytes for bcrypt comparison
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            truncated_bytes = password_bytes[:72]
            while truncated_bytes:
                try:
                    password = truncated_bytes.decode('utf-8')
                    break
                except UnicodeDecodeError:
                    truncated_bytes = truncated_bytes[:-1]
        
        if pwd_context.verify(password, user['hashed_password']):
            return {
                "success": True, 
                "user_id": user['id'], 
                "username": user['username'], 
                "email": user['email']
            }
        else:
            return {"success": False, "error": "Invalid credentials"}
            
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
        
    finally:
        cur.close()
        conn.close()