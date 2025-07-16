#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Enterprise SCIM User Creation Script

This script reads a CSV file containing user information and creates users 
via the GitHub Enterprise SCIM API.
"""

import csv
import json
import requests
import argparse
import logging
from typing import Dict, List, Optional, Any
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_scim.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("github_scim")

class GithubScimClient:
    """Client for interacting with GitHub Enterprise SCIM API."""
    
    def __init__(self, base_url: str, access_token: str):
        """
        Initialize the SCIM client.
        
        Args:
            base_url: The base URL for the GitHub Enterprise instance
            access_token: The access token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/scim+json",
            "Accept": "application/scim+json"
        }
        self.scim_endpoint = f"{self.base_url}/scim/v2/enterprises/xfusion-digital-technologies/Users"

    def _make_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict:
        """
        Make an HTTP request to the SCIM API.
        
        Args:
            method: The HTTP method (GET, POST, PUT, DELETE)
            url: The URL to make the request to
            data: The request payload
            
        Returns:
            The response as a dictionary
        """
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            # Return empty dict for 204 No Content responses
            if response.status_code == 204:
                return {}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def list_users(self, filter_str: Optional[str] = None) -> List[Dict]:
        """
        List users from GitHub SCIM.
        
        Args:
            filter_str: Optional filter string
            
        Returns:
            List of user dictionaries
        """
        url = self.scim_endpoint
        if filter_str:
            url += f"?filter={filter_str}"
        
        response = self._make_request("GET", url)
        return response.get("Resources", [])
    
    def get_user(self, username: str) -> Optional[Dict]:
        """
        Get a user by username.
        
        Args:
            username: The username to look up
            
        Returns:
            User dictionary if found, None otherwise
        """
        users = self.list_users(f'userName eq "{username}"')
        return users[0] if users else None
    
    def get_user_by_id(self, user_id: str) -> Dict:
        """
        Get a user by their SCIM ID.
        
        Args:
            user_id: The SCIM user ID
            
        Returns:
            User dictionary
        """
        url = f"{self.scim_endpoint}/{user_id}"
        return self._make_request("GET", url)
    
    def create_user(self, user_data: Dict) -> Dict:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user data
            
        Returns:
            Created user dictionary
        """
        logger.info(f"Creating user: {user_data['userName']}")
        logger.info(f"User data: {json.dumps(user_data, indent=2)}")
        logger.info(f"SCIM endpoint: {self.scim_endpoint}")
        return self._make_request("POST", self.scim_endpoint, user_data)
    
    # Update and delete methods removed as per requirements - script only creates users


def read_csv_file(filepath: str) -> List[Dict]:
    """
    Read user data from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of dictionaries containing user data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    users = []
    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Process email field which may contain multiple comma-separated emails
                if 'emails' in row and row['emails']:
                    # Split emails by semicolon or other delimiter as needed
                    email_list = [email.strip() for email in row['emails'].split(';')]
                    row['emails'] = [{"value": email, "type": "work", "primary": True} for email in email_list]
                
                # Process roles field which may contain multiple comma-separated roles
                if 'roles' in row and row['roles']:
                    # Split roles by semicolon or other delimiter as needed
                    role_list = [role.strip() for role in row['roles'].split(';')]
                    row['roles'] = role_list[0]
                
                users.append(row)
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise
    
    return users


def format_user_for_scim(user_data: Dict) -> Dict:
    """
    Format user data according to SCIM schema.
    
    Args:
        user_data: Dictionary containing raw user data
        
    Returns:
        Formatted user data according to SCIM schema
    """
    scim_user = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "externalId": user_data.get("userName", ""),
        "active": True,
        "userName": user_data.get("userName", ""),
        "displayName": user_data.get("displayName", ""),
        "emails": user_data.get("emails", []),
        "roles": [
            {
                "value": user_data.get("roles", "user"),
                "primary": True
            }
        ]
    }
    return scim_user


def process_users(client: GithubScimClient, users: List[Dict]) -> None:
    """
    Process users to create them in GitHub Enterprise via SCIM.
    
    Args:
        client: GithubScimClient instance
        users: List of user dictionaries
    """
    for user_data in users:
        username = user_data.get("userName")
        if not username:
            logger.warning("Skipping user with missing userName")
            continue
        
        try:
            existing_user = client.get_user(username)
            
            if existing_user:
                logger.info(f"User {username} already exists, skipping creation")
            else:
                scim_user = format_user_for_scim(user_data)
                created_user = client.create_user(scim_user)
                logger.info(f"Created user {username} with ID {created_user.get('id')}")
            
        except Exception as e:
            logger.error(f"Error processing user {username}: {e}")


def main():
    """Main function to handle command line arguments and execute operations."""
    parser = argparse.ArgumentParser(description="GitHub Enterprise SCIM User Management")
    parser.add_argument("--csv", required=True, help="Path to the CSV file containing user data")
    parser.add_argument("--url", required=True, help="GitHub Enterprise URL")
    parser.add_argument("--token", required=True, help="GitHub OAuth token with SCIM scope")
    
    args = parser.parse_args()
    
    try:
        # Read user data from CSV
        users = read_csv_file(args.csv)
        
        if not users:
            logger.warning("No users found in CSV file")
            return
            
        # Initialize SCIM client
        client = GithubScimClient(args.url, args.token)
        
        # Process users (create only)
        process_users(client, users)
        
        logger.info("Successfully completed user creation operation")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
