"""
User authentication and access control system for the Suppliers AI platform.
Provides role-based access, session management, and activity logging.
"""
import streamlit as st
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os

class UserManager:
    """Comprehensive user management with authentication and roles"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.session_timeout = timedelta(hours=8)  # 8-hour sessions
        
        # Initialize default admin user if none exists
        self._ensure_admin_user()
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, any]:
        """
        Authenticate user credentials
        
        Returns:
            {
                'success': bool,
                'user': dict,
                'session_token': str,
                'message': str
            }
        """
        if not self.supabase:
            return self._mock_authentication(username, password)
        
        try:
            # Hash password for comparison
            password_hash = self._hash_password(password)
            
            # Query user from database
            result = self.supabase.table('users').select('*').eq('username', username).eq('password_hash', password_hash).execute()
            
            if result.data and len(result.data) > 0:
                user = result.data[0]
                
                # Check if user is active
                if not user.get('is_active', True):
                    return {
                        'success': False,
                        'message': 'Account is deactivated. Contact administrator.'
                    }
                
                # Generate session token
                session_token = self._generate_session_token()
                
                # Update last login
                self.supabase.table('users').update({
                    'last_login': datetime.now().isoformat(),
                    'session_token': session_token
                }).eq('id', user['id']).execute()
                
                # Log login activity
                self._log_activity(user['id'], 'login', {'ip_address': st.session_state.get('client_ip', 'unknown')})
                
                return {
                    'success': True,
                    'user': user,
                    'session_token': session_token,
                    'message': f'Welcome back, {user["display_name"]}!'
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid username or password.'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Authentication error: {str(e)}'
            }
    
    def create_user(self, username: str, password: str, email: str, display_name: str, 
                   role: str = 'user') -> Dict[str, any]:
        """
        Create new user account
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: User email
            display_name: Display name for UI
            role: User role (admin, manager, user, readonly)
        """
        if not self.supabase:
            return {'success': False, 'message': 'Database not available'}
        
        try:
            # Check if username already exists
            existing = self.supabase.table('users').select('id').eq('username', username).execute()
            if existing.data:
                return {'success': False, 'message': 'Username already exists'}
            
            # Check if email already exists
            existing_email = self.supabase.table('users').select('id').eq('email', email).execute()
            if existing_email.data:
                return {'success': False, 'message': 'Email already registered'}
            
            # Create user record
            user_data = {
                'username': username,
                'password_hash': self._hash_password(password),
                'email': email,
                'display_name': display_name,
                'role': role,
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                self._log_activity(user['id'], 'user_created', {'created_by': 'system'})
                
                return {
                    'success': True,
                    'user': user,
                    'message': f'User {username} created successfully'
                }
            else:
                return {'success': False, 'message': 'Failed to create user'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error creating user: {str(e)}'}
    
    def validate_session(self, user_id: str, session_token: str) -> bool:
        """Validate user session token"""
        if not self.supabase:
            return True  # Mock validation in development
        
        try:
            result = self.supabase.table('users').select('session_token, last_login').eq('id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                
                # Check if session token matches
                if user_data.get('session_token') != session_token:
                    return False
                
                # Check if session is not expired
                last_login = datetime.fromisoformat(user_data['last_login'])
                if datetime.now() - last_login > self.session_timeout:
                    return False
                
                return True
            
            return False
        except Exception:
            return False
    
    def get_user_permissions(self, role: str) -> List[str]:
        """Get permissions for a user role"""
        permissions = {
            'admin': [
                'view_all_data',
                'create_users',
                'manage_users',
                'delete_data',
                'export_data',
                'manage_system',
                'view_analytics',
                'process_documents',
                'approve_documents'
            ],
            'manager': [
                'view_all_data',
                'export_data',
                'view_analytics',
                'process_documents',
                'approve_documents'
            ],
            'user': [
                'view_own_data',
                'process_documents',
                'export_limited'
            ],
            'readonly': [
                'view_own_data'
            ]
        }
        return permissions.get(role, [])
    
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        user_permissions = self.get_user_permissions(user_role)
        return required_permission in user_permissions
    
    def logout_user(self, user_id: str) -> None:
        """Log out user and invalidate session"""
        if self.supabase:
            try:
                self.supabase.table('users').update({
                    'session_token': None
                }).eq('id', user_id).execute()
                
                self._log_activity(user_id, 'logout')
            except Exception:
                pass
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('users').select('id, username, email, display_name, role, is_active, created_at, last_login').execute()
            return result.data or []
        except Exception:
            return []
    
    def update_user(self, user_id: str, updates: Dict[str, any]) -> bool:
        """Update user information"""
        if not self.supabase:
            return False
        
        try:
            # Don't allow updating sensitive fields without proper handling
            safe_updates = {k: v for k, v in updates.items() 
                          if k in ['display_name', 'email', 'role', 'is_active']}
            
            if 'password' in updates:
                safe_updates['password_hash'] = self._hash_password(updates['password'])
            
            result = self.supabase.table('users').update(safe_updates).eq('id', user_id).execute()
            
            if result.data:
                self._log_activity(user_id, 'user_updated', {'fields': list(safe_updates.keys())})
                return True
            
            return False
        except Exception:
            return False
    
    def _ensure_admin_user(self):
        """Ensure default admin user exists"""
        if not self.supabase:
            return
        
        try:
            # Check if any admin user exists
            result = self.supabase.table('users').select('id').eq('role', 'admin').execute()
            
            if not result.data:
                # Create default admin user
                self.create_user(
                    username='admin',
                    password='admin123',  # Should be changed on first login
                    email='admin@supplier-agent.com',
                    display_name='Administrator',
                    role='admin'
                )
        except Exception:
            pass
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = "suppliers_ai_salt"  # In production, use random salt per user
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _log_activity(self, user_id: str, action: str, details: Dict = None):
        """Log user activity"""
        if not self.supabase:
            return
        
        try:
            activity_data = {
                'user_id': user_id,
                'action': action,
                'details': json.dumps(details or {}),
                'timestamp': datetime.now().isoformat(),
                'ip_address': st.session_state.get('client_ip', 'unknown')
            }
            
            self.supabase.table('user_activity').insert(activity_data).execute()
        except Exception:
            pass
    
    def _mock_authentication(self, username: str, password: str) -> Dict[str, any]:
        """Mock authentication for development"""
        mock_users = {
            'admin': {'password': 'admin', 'role': 'admin', 'display_name': 'Administrator'},
            'manager': {'password': 'manager', 'role': 'manager', 'display_name': 'Manager'},
            'user': {'password': 'user', 'role': 'user', 'display_name': 'User'}
        }
        
        if username in mock_users and mock_users[username]['password'] == password:
            return {
                'success': True,
                'user': {
                    'id': f'mock_{username}',
                    'username': username,
                    'role': mock_users[username]['role'],
                    'display_name': mock_users[username]['display_name']
                },
                'session_token': f'mock_token_{username}',
                'message': f'Welcome {mock_users[username]["display_name"]}!'
            }
        
        return {
            'success': False,
            'message': 'Invalid credentials. Try: admin/admin, manager/manager, or user/user'
        }


def require_authentication():
    """Decorator/function to require authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
        return False
    return True

def show_login_page():
    """Display login interface"""
    st.title("🔐 Login Required")
    st.markdown("Please log in to access the AI Supplier Agent")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username and password:
                # Initialize user manager
                user_manager = UserManager()
                
                # Attempt authentication
                auth_result = user_manager.authenticate_user(username, password)
                
                if auth_result['success']:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.user = auth_result['user']
                    st.session_state.session_token = auth_result['session_token']
                    
                    st.success(auth_result['message'])
                    st.rerun()
                else:
                    st.error(auth_result['message'])
            else:
                st.error("Please enter both username and password")
    
    # Show demo credentials
    with st.expander("Demo Credentials"):
        st.markdown("""
        **Demo Users:**
        - **Admin**: username: `admin`, password: `admin`
        - **Manager**: username: `manager`, password: `manager`  
        - **User**: username: `user`, password: `user`
        """)

def show_user_menu():
    """Show user menu in sidebar"""
    if st.session_state.get('authenticated'):
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **{st.session_state.user['display_name']}**")
            st.markdown(f"Role: {st.session_state.user['role'].title()}")
            
            if st.button("🚪 Logout", key="logout_btn"):
                # Clear session
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.session_token = None
                st.rerun()

def check_permission(required_permission: str) -> bool:
    """Check if current user has required permission"""
    if not st.session_state.get('authenticated'):
        return False
    
    user_manager = UserManager()
    user_role = st.session_state.user.get('role', 'user')
    return user_manager.check_permission(user_role, required_permission)

# Global user manager instance
user_manager = UserManager()