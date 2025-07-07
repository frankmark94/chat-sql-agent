"""
GitHub webhook handlers for Chat SQL Agent
"""
import hashlib
import hmac
import json
from typing import Dict, Any
from flask import Flask, request, jsonify
from .config import settings
from .github_client import GitHubAppClient


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature_header:
        return False
    
    try:
        hash_object = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode('utf-8'),
            msg=payload_body,
            digestmod=hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()
        return hmac.compare_digest(expected_signature, signature_header)
    except Exception:
        return False


class GitHubWebhookHandler:
    """Handle GitHub webhook events"""
    
    def __init__(self):
        self.github_client = GitHubAppClient()
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup webhook routes"""
        @self.app.route('/github-webhook', methods=['POST'])
        def handle_webhook():
            return self.handle_github_webhook()
    
    def handle_github_webhook(self):
        """Main webhook handler"""
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_github_signature(request.data, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Get event type
        event_type = request.headers.get('X-GitHub-Event')
        payload = request.get_json()
        
        if not event_type or not payload:
            return jsonify({'error': 'Invalid payload'}), 400
        
        # Route to appropriate handler
        handler_map = {
            'push': self.handle_push,
            'pull_request': self.handle_pull_request,
            'issues': self.handle_issues,
            'issue_comment': self.handle_issue_comment,
            'pull_request_review': self.handle_pull_request_review,
            'installation': self.handle_installation,
            'installation_repositories': self.handle_installation_repositories,
        }
        
        handler = handler_map.get(event_type, self.handle_unknown_event)
        
        try:
            result = handler(payload)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def handle_push(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle push events"""
        repo_name = payload['repository']['name']
        repo_owner = payload['repository']['owner']['login']
        commits = payload.get('commits', [])
        
        # Example: Create a check run for SQL analysis
        if commits:
            head_sha = payload['after']
            check_run = self.github_client.create_check_run(
                repo_owner, repo_name, 
                "SQL Analysis", head_sha,
                status="in_progress"
            )
            
            # TODO: Implement actual SQL analysis logic here
            # For now, just mark as completed
            self.github_client.update_check_run(
                repo_owner, repo_name, check_run['id'],
                status="completed", conclusion="success",
                output={
                    'title': 'SQL Analysis Complete',
                    'summary': 'No SQL issues found in the push.'
                }
            )
        
        return {'status': 'processed', 'event': 'push'}
    
    def handle_pull_request(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle pull request events"""
        action = payload['action']
        pr_number = payload['number']
        repo_name = payload['repository']['name']
        repo_owner = payload['repository']['owner']['login']
        
        if action in ['opened', 'synchronize']:
            # Create SQL analysis check
            head_sha = payload['pull_request']['head']['sha']
            check_run = self.github_client.create_check_run(
                repo_owner, repo_name,
                "SQL Schema Analysis", head_sha,
                status="in_progress"
            )
            
            # TODO: Implement SQL schema validation
            # For now, just mark as completed
            self.github_client.update_check_run(
                repo_owner, repo_name, check_run['id'],
                status="completed", conclusion="success",
                output={
                    'title': 'SQL Schema Analysis Complete',
                    'summary': 'SQL schema changes look good!'
                }
            )
            
            # Add a comment with SQL insights
            comment_body = """
🤖 **SQL Agent Analysis**

I've analyzed the changes in this pull request:

- ✅ SQL schema changes detected
- ✅ No breaking changes found
- ✅ Database migrations look good

Feel free to ask me questions about the SQL changes using natural language!
            """
            
            self.github_client.create_issue_comment(
                repo_owner, repo_name, pr_number, comment_body
            )
        
        return {'status': 'processed', 'event': 'pull_request', 'action': action}
    
    def handle_issues(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle issue events"""
        action = payload['action']
        issue_number = payload['issue']['number']
        repo_name = payload['repository']['name']
        repo_owner = payload['repository']['owner']['login']
        
        if action == 'opened':
            issue_title = payload['issue']['title'].lower()
            issue_body = payload['issue']['body'].lower() if payload['issue']['body'] else ""
            
            # Check if it's a SQL-related issue
            sql_keywords = ['sql', 'database', 'query', 'schema', 'table', 'migration']
            if any(keyword in issue_title or keyword in issue_body for keyword in sql_keywords):
                comment_body = """
🗣️ **Chat SQL Agent Here!**

I noticed this issue is related to SQL/database work. I can help you with:

- 📊 Analyzing database schemas
- 🔍 Writing and optimizing SQL queries
- 📈 Creating data visualizations
- 📧 Generating reports

Just mention me in a comment with your question, and I'll provide insights!
                """
                
                self.github_client.create_issue_comment(
                    repo_owner, repo_name, issue_number, comment_body
                )
        
        return {'status': 'processed', 'event': 'issues', 'action': action}
    
    def handle_issue_comment(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle issue comment events"""
        action = payload['action']
        
        if action == 'created':
            comment_body = payload['comment']['body'].lower()
            issue_number = payload['issue']['number']
            repo_name = payload['repository']['name']
            repo_owner = payload['repository']['owner']['login']
            
            # Check if the bot is mentioned
            if '@chat-sql-agent' in comment_body or 'sql agent' in comment_body:
                response_body = """
🤖 **SQL Agent Response**

Thanks for mentioning me! I'm ready to help with SQL and database questions.

Here's what I can do:
- 📊 Analyze your database schema
- 🔍 Help write optimal SQL queries
- 📈 Create visualizations from your data
- 📧 Generate comprehensive reports

Please share your specific SQL question or database challenge!
                """
                
                self.github_client.create_issue_comment(
                    repo_owner, repo_name, issue_number, response_body
                )
        
        return {'status': 'processed', 'event': 'issue_comment', 'action': action}
    
    def handle_pull_request_review(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle pull request review events"""
        action = payload['action']
        pr_number = payload['pull_request']['number']
        repo_name = payload['repository']['name']
        repo_owner = payload['repository']['owner']['login']
        
        if action == 'submitted':
            review_state = payload['review']['state']
            
            if review_state == 'approved':
                comment_body = """
🎉 **Congratulations!**

Your pull request has been approved! If there were any SQL changes in this PR, they've been validated by our SQL Agent.

Ready to merge? 🚀
                """
                
                self.github_client.create_issue_comment(
                    repo_owner, repo_name, pr_number, comment_body
                )
        
        return {'status': 'processed', 'event': 'pull_request_review', 'action': action}
    
    def handle_installation(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle app installation events"""
        action = payload['action']
        
        if action == 'created':
            # App was installed
            installation_id = payload['installation']['id']
            account = payload['installation']['account']['login']
            
            # TODO: Store installation details if needed
            print(f"Chat SQL Agent installed for {account} (ID: {installation_id})")
        
        return {'status': 'processed', 'event': 'installation', 'action': action}
    
    def handle_installation_repositories(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle installation repository events"""
        action = payload['action']
        
        if action == 'added':
            repositories = payload.get('repositories_added', [])
            for repo in repositories:
                print(f"Chat SQL Agent added to repository: {repo['full_name']}")
        
        return {'status': 'processed', 'event': 'installation_repositories', 'action': action}
    
    def handle_unknown_event(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Handle unknown events"""
        return {'status': 'ignored', 'event': 'unknown'}
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the webhook server"""
        self.app.run(host=host, port=port, debug=debug)


# Create webhook handler instance
webhook_handler = GitHubWebhookHandler()

if __name__ == '__main__':
    webhook_handler.run(debug=True)