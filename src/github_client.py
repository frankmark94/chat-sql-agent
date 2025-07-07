"""
GitHub App client for Chat SQL Agent
"""
import jwt
import time
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
from .config import settings


class GitHubAppClient:
    """GitHub App client for authentication and API interactions"""
    
    def __init__(self):
        self.app_id = settings.GITHUB_APP_ID
        self.private_key = settings.GITHUB_APP_PRIVATE_KEY
        self.installation_id = settings.GITHUB_APP_INSTALLATION_ID
        self.base_url = "https://api.github.com"
        
    def generate_jwt(self) -> str:
        """Generate JWT token for GitHub App authentication"""
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + 600,  # 10 minutes
            'iss': self.app_id
        }
        
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    def get_installation_access_token(self) -> str:
        """Get installation access token"""
        jwt_token = self.generate_jwt()
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.base_url}/app/installations/{self.installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        return response.json()['token']
    
    def get_authenticated_headers(self) -> Dict[str, str]:
        """Get headers with installation access token"""
        token = self.get_installation_access_token()
        return {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def create_issue_comment(self, repo_owner: str, repo_name: str, issue_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on an issue or pull request"""
        headers = self.get_authenticated_headers()
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
        
        data = {'body': body}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def create_check_run(self, repo_owner: str, repo_name: str, name: str, head_sha: str, 
                        status: str = "in_progress", conclusion: Optional[str] = None) -> Dict[str, Any]:
        """Create a check run"""
        headers = self.get_authenticated_headers()
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/check-runs"
        
        data = {
            'name': name,
            'head_sha': head_sha,
            'status': status
        }
        
        if conclusion:
            data['conclusion'] = conclusion
            
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def update_check_run(self, repo_owner: str, repo_name: str, check_run_id: int, 
                        status: str, conclusion: Optional[str] = None, 
                        output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update a check run"""
        headers = self.get_authenticated_headers()
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/check-runs/{check_run_id}"
        
        data = {'status': status}
        
        if conclusion:
            data['conclusion'] = conclusion
        if output:
            data['output'] = output
            
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_pull_request(self, repo_owner: str, repo_name: str, pull_number: int) -> Dict[str, Any]:
        """Get pull request details"""
        headers = self.get_authenticated_headers()
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pull_number}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_repository(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository details"""
        headers = self.get_authenticated_headers()
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()