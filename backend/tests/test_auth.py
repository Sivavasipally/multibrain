"""
Tests for authentication endpoints
"""

import pytest
import json
from models import User


class TestAuthEndpoints:
    """Test authentication-related endpoints."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        response_data = json.loads(response.data)
        
        assert 'access_token' in response_data
        assert 'user' in response_data
        assert response_data['user']['username'] == 'newuser'
        assert response_data['user']['email'] == 'newuser@example.com'
        assert 'password' not in response_data['user']
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        data = {
            'username': 'newuser',
            # Missing email and password
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        data = {
            'username': test_user.username,
            'email': 'different@example.com',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Username already exists' in response_data['error']
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        data = {
            'username': 'differentuser',
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Email already exists' in response_data['error']
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        data = {
            'username': test_user.username,
            'password': 'testpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'access_token' in response_data
        assert 'user' in response_data
        assert response_data['user']['username'] == test_user.username
    
    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert 'Invalid credentials' in response_data['error']
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        data = {
            'username': test_user.username,
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert 'Invalid credentials' in response_data['error']
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        data = {
            'username': 'testuser'
            # Missing password
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Missing username or password' in response_data['error']
    
    def test_get_profile_success(self, client, auth_headers, test_user):
        """Test successful profile retrieval."""
        response = client.get('/api/auth/profile', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'user' in response_data
        assert response_data['user']['id'] == test_user.id
        assert response_data['user']['username'] == test_user.username
        assert response_data['user']['email'] == test_user.email
    
    def test_get_profile_no_token(self, client):
        """Test profile retrieval without authentication token."""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401
    
    def test_get_profile_invalid_token(self, client):
        """Test profile retrieval with invalid token."""
        headers = {
            'Authorization': 'Bearer invalid-token',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 422  # JWT decode error
    
    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
    
    def test_logout_no_token(self, client):
        """Test logout without authentication token."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self):
        """Test user model creation."""
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpassword')
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash is not None
        assert user.password_hash != 'testpassword'  # Should be hashed
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        user = User(username='test', email='test@example.com')
        password = 'testpassword123'
        
        user.set_password(password)
        
        # Password should be hashed
        assert user.password_hash != password
        
        # Should verify correct password
        assert user.check_password(password) is True
        
        # Should reject incorrect password
        assert user.check_password('wrongpassword') is False
    
    def test_user_to_dict(self, test_user):
        """Test user serialization to dictionary."""
        user_dict = test_user.to_dict()
        
        expected_keys = ['id', 'username', 'email', 'created_at', 'is_active']
        for key in expected_keys:
            assert key in user_dict
        
        # Should not include sensitive data
        assert 'password_hash' not in user_dict
        assert 'password' not in user_dict
        
        assert user_dict['username'] == test_user.username
        assert user_dict['email'] == test_user.email
        assert user_dict['is_active'] is True


class TestAuthIntegration:
    """Integration tests for authentication flow."""
    
    def test_register_login_profile_flow(self, client):
        """Test complete registration -> login -> profile flow."""
        # 1. Register new user
        register_data = {
            'username': 'flowtest',
            'email': 'flowtest@example.com',
            'password': 'password123'
        }
        
        register_response = client.post('/api/auth/register',
                                      data=json.dumps(register_data),
                                      content_type='application/json')
        
        assert register_response.status_code == 201
        register_data = json.loads(register_response.data)
        token = register_data['access_token']
        
        # 2. Use token to get profile
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        profile_response = client.get('/api/auth/profile', headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = json.loads(profile_response.data)
        assert profile_data['user']['username'] == 'flowtest'
        
        # 3. Login with same credentials
        login_data = {
            'username': 'flowtest',
            'password': 'password123'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        assert login_response.status_code == 200
        login_response_data = json.loads(login_response.data)
        
        # Should get a new token
        assert 'access_token' in login_response_data
        assert login_response_data['user']['username'] == 'flowtest'
