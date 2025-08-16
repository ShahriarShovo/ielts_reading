# NEW FILE: Shared Authentication Permission for microservices
# This permission verifies JWT tokens by calling the authentication project's shared service

import requests
from rest_framework.permissions import BasePermission
from django.conf import settings
import logging

# CHANGED: Use the correct logger name that matches settings
logger = logging.getLogger('reading')

class SharedAuthPermission(BasePermission):
    """
    Shared Authentication Permission for microservices communication.
    
    This permission class:
    1. Extracts JWT tokens from the Authorization header
    2. Calls the authentication project's shared service to verify the token
    3. Stores user information in the request object for use in views
    4. Returns True if token is valid, False otherwise
    
    This enables microservices to share authentication without duplicating
    JWT verification logic or sharing secret keys between services.
    
    Usage:
    - Add to permission_classes in views that need authentication
    - Works with Shared Authentication Service in the auth project
    """
    
    def has_permission(self, request, view):
        """
        Verify JWT token by calling the authentication project's shared service.
        
        This method:
        1. Extracts the Bearer token from Authorization header
        2. Makes HTTP request to authentication project's verify-token endpoint
        3. Stores user info (user_id, organization_id, user_email) in request object
        4. Returns True if token is valid, False otherwise
        
        Args:
            request: HTTP request object containing Authorization header
            view: The view being accessed
            
        Returns:
            bool: True if token is valid and user has permission, False otherwise
        """
        logger.info(f"=== SHARED AUTH PERMISSION CALLED ===")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request method: {request.method}")
        
        try:
            # Get JWT token from Authorization header (format: "Bearer <token>")
            auth_header = request.headers.get('Authorization')
            logger.info(f"Authorization header: {auth_header}")
            
            # Validate that Authorization header exists and has Bearer format
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.error("No Bearer token found in Authorization header")
                return False
            
            # Extract token from "Bearer <token>" format
            token = auth_header.split(' ')[1]
            logger.info(f"Extracted token: {token[:50]}...")  # Log first 50 chars for security
            
            # Call authentication project's shared service to verify token
            auth_service_url = 'http://127.0.0.1:8000/api/user/auth/verify-token/'
            logger.info(f"Calling auth service at: {auth_service_url}")
            
            logger.info(f"Sending request to auth service...")
            # Make HTTP POST request to authentication project
            response = requests.post(
                auth_service_url,
                json={'token': token},
                headers={'Content-Type': 'application/json'},
                timeout=10  # 10 second timeout to prevent hanging
            )
            
            logger.info(f"Auth service response status: {response.status_code}")
            logger.info(f"Auth service response: {response.text}")
            
            # If authentication was successful (200 status)
            if response.status_code == 200:
                # Parse the response and store user info in request object
                user_data = response.json()
                request.user_id = user_data.get('user_id')
                request.organization_id = user_data.get('organization_id')
                request.user_email = user_data.get('user_email')
                logger.info(f"Token verified successfully for user: {user_data.get('user_email')}")
                return True
            else:
                # Token verification failed
                logger.error(f"Token verification failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            # Handle network errors (auth service unavailable, timeout, etc.)
            logger.error(f"Error calling authentication service: {str(e)}")
            return False
        except Exception as e:
            # Handle any other unexpected errors
            logger.error(f"Shared auth permission error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
