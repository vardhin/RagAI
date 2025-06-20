from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
import os
import secrets
import hashlib
import asyncio
from email_validator import validate_email, EmailNotValidError
import re
import sqlite3
from pathlib import Path
import logging
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = Path("auth.db")

# Update the UserSignup model to be more flexible
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    full_name: str
    
    # Allow username as an alias for full_name
    @validator('full_name', pre=True)
    def set_full_name(cls, v, values):
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if not re.match(r"^[a-zA-Z\s]+$", v.strip()):
            raise ValueError('Full name must contain only letters and spaces')
        return v.strip()

class UserSignin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class AuthDatabase:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        """Initialize the authentication database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                password_reset_token TEXT,
                password_reset_expires TIMESTAMP
            )
        ''')
        
        # Login attempts table for rate limiting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Active tokens table for token blacklisting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                token_type TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_user(self, email: str, password_hash: str, full_name: str) -> int:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                (email.lower(), password_hash, full_name)
            )
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()
    
    def log_login_attempt(self, email: str, ip_address: str, success: bool):
        """Log login attempt"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO login_attempts (email, ip_address, success) VALUES (?, ?, ?)",
            (email.lower(), ip_address, success)
        )
        conn.commit()
        conn.close()
    
    def get_failed_login_attempts(self, email: str, minutes: int = None) -> int:
        """Get failed login attempts count"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if minutes:
            cursor.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE email = ? AND success = FALSE 
                AND attempted_at > datetime('now', '-{} minutes')
            '''.format(minutes), (email.lower(),))
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM login_attempts WHERE email = ? AND success = FALSE",
                (email.lower(),)
            )
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear_login_attempts(self, email: str):
        """Clear login attempts for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM login_attempts WHERE email = ?", (email.lower(),))
        conn.commit()
        conn.close()
    
    def store_token(self, user_id: int, token: str, token_type: str, expires_at: datetime):
        """Store active token"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO active_tokens (user_id, token_hash, token_type, expires_at) VALUES (?, ?, ?, ?)",
            (user_id, token_hash, token_type, expires_at)
        )
        conn.commit()
        conn.close()
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM active_tokens WHERE token_hash = ? AND expires_at > CURRENT_TIMESTAMP",
            (token_hash,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0
    
    def revoke_token(self, token: str):
        """Revoke a token"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM active_tokens WHERE token_hash = ?", (token_hash,))
        conn.commit()
        conn.close()
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM active_tokens WHERE expires_at <= CURRENT_TIMESTAMP")
        cursor.execute("DELETE FROM login_attempts WHERE attempted_at < datetime('now', '-7 days')")
        conn.commit()
        conn.close()

# Initialize database
auth_db = AuthDatabase()

class AuthManager:
    def __init__(self):
        self.db = auth_db
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access"):
        """Verify JWT token"""
        try:
            # Check if token is blacklisted
            if self.db.is_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
    
    async def signup(self, user_data: UserSignup, request: Request) -> TokenResponse:
        """User signup"""
        try:
            # Additional email validation
            validate_email(user_data.email)
        except EmailNotValidError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Hash password
        password_hash = self.hash_password(user_data.password)
        
        # Create user
        user_id = self.db.create_user(
            email=user_data.email,
            password_hash=password_hash,
            full_name=user_data.full_name
        )
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = self.create_access_token(
            data={"sub": str(user_id), "email": user_data.email},
            expires_delta=access_token_expires
        )
        refresh_token = self.create_refresh_token(
            data={"sub": str(user_id), "email": user_data.email},
            expires_delta=refresh_token_expires
        )
        
        # Store tokens
        self.db.store_token(user_id, access_token, "access", datetime.utcnow() + access_token_expires)
        self.db.store_token(user_id, refresh_token, "refresh", datetime.utcnow() + refresh_token_expires)
        
        # Update last login
        self.db.update_last_login(user_id)
        
        # Log successful signup
        ip_address = self.get_client_ip(request)
        self.db.log_login_attempt(user_data.email, ip_address, True)
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def signin(self, user_data: UserSignin, request: Request) -> TokenResponse:
        """User signin"""
        ip_address = self.get_client_ip(request)
        
        # Check for account lockout
        failed_attempts = self.db.get_failed_login_attempts(
            user_data.email, LOCKOUT_DURATION_MINUTES
        )
        
        if failed_attempts >= MAX_LOGIN_ATTEMPTS:
            self.db.log_login_attempt(user_data.email, ip_address, False)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked due to too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
            )
        
        # Get user
        user = self.db.get_user_by_email(user_data.email)
        if not user:
            self.db.log_login_attempt(user_data.email, ip_address, False)
            await asyncio.sleep(0.5)  # Prevent timing attacks
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user["is_active"]:
            self.db.log_login_attempt(user_data.email, ip_address, False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Verify password
        if not self.verify_password(user_data.password, user["password_hash"]):
            self.db.log_login_attempt(user_data.email, ip_address, False)
            await asyncio.sleep(0.5)  # Prevent timing attacks
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Clear failed login attempts
        self.db.clear_login_attempts(user_data.email)
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = self.create_access_token(
            data={"sub": str(user["id"]), "email": user["email"]},
            expires_delta=access_token_expires
        )
        refresh_token = self.create_refresh_token(
            data={"sub": str(user["id"]), "email": user["email"]},
            expires_delta=refresh_token_expires
        )
        
        # Store tokens
        self.db.store_token(user["id"], access_token, "access", datetime.utcnow() + access_token_expires)
        self.db.store_token(user["id"], refresh_token, "refresh", datetime.utcnow() + refresh_token_expires)
        
        # Update last login
        self.db.update_last_login(user["id"])
        
        # Log successful login
        self.db.log_login_attempt(user_data.email, ip_address, True)
        
        logger.info(f"User logged in successfully: {user_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def refresh_token(self, refresh_token_request: RefreshTokenRequest) -> TokenResponse:
        """Refresh access token"""
        payload = self.verify_token(refresh_token_request.refresh_token, "refresh")
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        
        # Get user to ensure still active
        user = self.db.get_user_by_id(user_id)
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": str(user_id), "email": email},
            expires_delta=access_token_expires
        )
        
        # Store new token
        self.db.store_token(user_id, access_token, "access", datetime.utcnow() + access_token_expires)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_request.refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def logout(self, token: str):
        """Logout user and revoke token"""
        self.db.revoke_token(token)
        logger.info("User logged out successfully")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
        """Get current authenticated user"""
        payload = self.verify_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        return UserProfile(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            is_active=user["is_active"],
            created_at=datetime.fromisoformat(user["created_at"]),
            last_login=datetime.fromisoformat(user["last_login"]) if user["last_login"] else None
        )

# Initialize auth manager
auth_manager = AuthManager()

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """Dependency to get current authenticated user"""
    return await auth_manager.get_current_user(credentials)

async def get_current_active_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# Middleware for rate limiting and security headers
class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

# Cleanup task
async def cleanup_expired_data():
    """Periodic cleanup of expired tokens and old login attempts"""
    while True:
        try:
            auth_db.cleanup_expired_tokens()
            logger.info("Cleaned up expired tokens and old login attempts")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # Run cleanup every hour
        await asyncio.sleep(3600)