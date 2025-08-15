"""
JWT Authentication system for Agar.io game.
Handles user registration, login, password reset, and session management.
"""

import os
import jwt
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr

from models import Player, PlayerCreate, PlayerLogin, Token, TokenData, PasswordReset, PasswordResetConfirm

logger = logging.getLogger(__name__)

class AuthConfig:
    """Authentication configuration"""
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key-change-in-production')
    ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '1440'))  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('JWT_REFRESH_EXPIRE_DAYS', '30'))

class PasswordHasher:
    """Handles password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

class TokenManager:
    """Manages JWT token creation and validation"""
    
    def __init__(self):
        self.config = AuthConfig()
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({'exp': expire, 'type': 'access'})
        
        return jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({'exp': expire, 'type': 'refresh'})
        
        return jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.SECRET_KEY, algorithms=[self.config.ALGORITHM])
            
            # Check token type
            if payload.get('type') != token_type:
                return None
            
            user_id = payload.get('sub')
            username = payload.get('username')
            role = payload.get('role', 'user')
            exp = payload.get('exp')
            
            if user_id is None or username is None:
                return None
            
            return TokenData(user_id=user_id, username=username, role=role, exp=exp)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT error: {e}")
            return None
    
    def create_password_reset_token(self, user_id: str) -> str:
        """Create password reset token"""
        data = {'sub': user_id, 'type': 'password_reset'}
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        data.update({'exp': expire})
        
        return jwt.encode(data, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)

class AuthService:
    """Authentication service"""
    
    def __init__(self, database):
        self.database = database
        self.token_manager = TokenManager()
        self.password_hasher = PasswordHasher()
    
    async def register_user(self, user_data: PlayerCreate) -> Player:
        """Register a new user"""
        try:
            # Check if user already exists
            if user_data.email:
                existing_user = await self.database.get_player_by_email(user_data.email)
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            # Check if username is taken
            existing_user = await self.database.get_player_by_name(user_data.name)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            
            # Hash password if provided
            password_hash = None
            if user_data.password:
                password_hash = self.password_hasher.hash_password(user_data.password)
            
            # Create user
            player = Player(
                name=user_data.name,
                display_name=user_data.name,
                email=user_data.email,
                password_hash=password_hash,
                createdAt=datetime.utcnow(),
                lastActiveAt=datetime.utcnow()
            )
            
            created_player = await self.database.create_player(player)
            logger.info(f"User registered: {created_player.name}")
            
            return created_player
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def authenticate_user(self, login_data: PlayerLogin) -> Optional[Player]:
        """Authenticate user login"""
        try:
            # Get user by email
            user = await self.database.get_player_by_email(login_data.email)
            if not user or not user.password_hash:
                return None
            
            # Check if user is banned
            if user.is_banned:
                if user.ban_expires_at and user.ban_expires_at > datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Account banned until {user.ban_expires_at}. Reason: {user.ban_reason}"
                    )
                elif not user.ban_expires_at:  # Permanent ban
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Account permanently banned. Reason: {user.ban_reason}"
                    )
            
            # Verify password
            if not self.password_hasher.verify_password(login_data.password, user.password_hash):
                return None
            
            # Update last active time
            await self.database.update_player(user.id, {
                'lastActiveAt': datetime.utcnow(),
                'isOnline': True
            })
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def create_tokens(self, user: Player) -> Token:
        """Create access and refresh tokens for user"""
        try:
            token_data = {
                'sub': user.id,
                'username': user.name,
                'role': user.role
            }
            
            access_token = self.token_manager.create_access_token(token_data)
            refresh_token = self.token_manager.create_refresh_token(token_data)
            
            return Token(
                access_token=access_token,
                token_type='bearer',
                expires_in=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_token=refresh_token
            )
            
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            token_data = self.token_manager.verify_token(refresh_token, 'refresh')
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Get user
            user = await self.database.get_player(token_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Create new tokens
            return await self.create_tokens(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token refresh failed"
            )
    
    async def initiate_password_reset(self, email: str) -> bool:
        """Initiate password reset process"""
        try:
            # Find user by email
            user = await self.database.get_player_by_email(email)
            if not user:
                # Return True anyway to prevent email enumeration
                return True
            
            # Generate reset token
            reset_token = self.token_manager.create_password_reset_token(user.id)
            
            # TODO: Send email with reset link
            # For now, we'll just log it (in development)
            reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
            logger.info(f"Password reset URL for {email}: {reset_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Password reset initiation error: {e}")
            return False
    
    async def reset_password(self, reset_data: PasswordResetConfirm) -> bool:
        """Reset user password using reset token"""
        try:
            # Verify reset token
            token_data = self.token_manager.verify_token(reset_data.token, 'password_reset')
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # Get user
            user = await self.database.get_player(token_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Hash new password
            new_password_hash = self.password_hasher.hash_password(reset_data.new_password)
            
            # Update password
            await self.database.update_player(user.id, {
                'password_hash': new_password_hash
            })
            
            logger.info(f"Password reset successful for user {user.id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return False
    
    async def logout_user(self, user_id: str) -> bool:
        """Logout user (mark as offline)"""
        try:
            await self.database.update_player(user_id, {
                'isOnline': False
            })
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

# FastAPI dependencies
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                          database=None) -> Player:
    """Get current authenticated user"""
    if not database:
        # This should be injected by the endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available"
        )
    
    try:
        token_manager = TokenManager()
        token_data = token_manager.verify_token(credentials.credentials)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await database.get_player(token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is banned
        if user.is_banned:
            if user.ban_expires_at and user.ban_expires_at > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account banned until {user.ban_expires_at}"
                )
            elif not user.ban_expires_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account permanently banned"
                )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_admin_user(current_user: Player = Depends(get_current_user)) -> Player:
    """Get current user and verify admin role"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                           database=None) -> Optional[Player]:
    """Get current user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, database)
    except HTTPException:
        return None

# Session management for WebSocket connections
class SessionManager:
    """Manages user sessions for WebSocket connections"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}  # user_id -> session_data
    
    def create_session(self, user_id: str, connection_id: str) -> None:
        """Create a new session"""
        self.active_sessions[user_id] = {
            'connection_id': connection_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
    
    def update_activity(self, user_id: str) -> None:
        """Update session activity"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]['last_activity'] = datetime.utcnow()
    
    def remove_session(self, user_id: str) -> None:
        """Remove session"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if user is online"""
        return user_id in self.active_sessions
    
    def get_active_users(self) -> List[str]:
        """Get list of active user IDs"""
        return list(self.active_sessions.keys())
    
    def cleanup_stale_sessions(self, timeout_minutes: int = 30) -> None:
        """Remove stale sessions"""
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        stale_users = [
            user_id for user_id, session in self.active_sessions.items()
            if session['last_activity'] < cutoff
        ]
        
        for user_id in stale_users:
            del self.active_sessions[user_id]

# Global session manager
session_manager = SessionManager()

# Global auth service (to be initialized with database)
auth_service = None

def initialize_auth_service(database):
    """Initialize auth service with database"""
    global auth_service
    auth_service = AuthService(database)