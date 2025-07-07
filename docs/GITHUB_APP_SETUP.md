# GitHub App Installation Guide

This guide walks you through setting up the Chat SQL Agent as a GitHub App for your repositories.

## 📋 Prerequisites

- GitHub account with admin access to your repositories
- Chat SQL Agent project set up locally
- Python environment with required dependencies

## 🔧 Step 1: Create GitHub App

1. **Navigate to GitHub App Creation**
   - Go to [GitHub Developer Settings](https://github.com/settings/developers)
   - Click "New GitHub App"

2. **Configure Basic Information**
   - **App Name**: `Chat SQL Agent` (or your preferred name)
   - **Description**: `AI-powered SQL analysis and database interaction`
   - **Homepage URL**: Your project repository URL
   - **Webhook URL**: `https://your-domain.com/github-webhook`
   - **Webhook Secret**: Generate a secure random string

3. **Set Repository Permissions**
   - **Actions**: Read
   - **Contents**: Read
   - **Issues**: Write
   - **Pull requests**: Write
   - **Metadata**: Read (required)
   - **Repository hooks**: Write
   - **Statuses**: Write
   - **Checks**: Write

4. **Subscribe to Events**
   - [x] Push
   - [x] Pull request
   - [x] Issues
   - [x] Issue comment
   - [x] Pull request review
   - [x] Pull request review comment
   - [x] Repository
   - [x] Installation
   - [x] Installation repositories

5. **Create the App**
   - Click "Create GitHub App"
   - Note down the **App ID** and **Installation ID**
   - Generate and download the **Private Key**

## 🏗️ Step 2: Configure Environment

1. **Update `.env` file**
   ```env
   # GitHub App Configuration
   GITHUB_APP_ID=your_app_id_here
   GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
   your_private_key_content_here
   -----END RSA PRIVATE KEY-----
   GITHUB_APP_INSTALLATION_ID=your_installation_id_here
   GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Step 3: Deploy Webhook Server

### Option A: Local Development (using ngrok)

1. **Install ngrok**
   ```bash
   # Download from https://ngrok.com/download
   # Or use package manager
   npm install -g ngrok
   ```

2. **Start Webhook Server**
   ```bash
   python -m src.github_webhooks
   ```

3. **Expose Local Server**
   ```bash
   ngrok http 5000
   ```

4. **Update Webhook URL**
   - Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
   - Update your GitHub App webhook URL to: `https://abc123.ngrok.io/github-webhook`

### Option B: Production Deployment

1. **Deploy to Cloud Platform**
   - **Heroku**: Use `Procfile` with `web: python -m src.github_webhooks`
   - **AWS/GCP/Azure**: Deploy Flask app with webhook endpoint
   - **Docker**: Use provided Dockerfile

2. **Configure Domain**
   - Set up SSL certificate
   - Update GitHub App webhook URL to your production domain

## 🔐 Step 4: Install GitHub App

1. **Install on Repositories**
   - Go to your GitHub App settings
   - Click "Install App"
   - Select repositories to install on
   - Complete installation

2. **Test Installation**
   - Create a test issue in your repository
   - Check if the app responds with SQL-related comments
   - Create a pull request to test check runs

## 🎯 Step 5: Features & Usage

Once installed, your GitHub App will:

### 🔍 **Pull Request Analysis**
- Automatically analyze SQL changes in pull requests
- Create check runs for SQL schema validation
- Comment on PRs with SQL insights

### 📝 **Issue Management**
- Detect SQL-related issues automatically
- Provide helpful SQL analysis and suggestions
- Respond to mentions (`@chat-sql-agent`)

### ⚡ **Push Events**
- Monitor SQL file changes
- Run automated SQL analysis
- Report issues via check runs

### 💬 **Interactive Comments**
- Mention the bot in comments: `@chat-sql-agent analyze this query`
- Get instant SQL insights and recommendations
- Ask questions about database schema changes

## 🛠️ Customization

### Modify Webhook Handlers

Edit `src/github_webhooks.py` to customize:

```python
def handle_pull_request(self, payload):
    # Add your custom PR analysis logic
    pass

def handle_issue_comment(self, payload):
    # Add your custom comment handling
    pass
```

### Configure SQL Analysis

Update the SQL analysis logic in the webhook handlers:

```python
# Example: Custom SQL validation
def validate_sql_changes(self, files_changed):
    # Implement your SQL validation logic
    return {"status": "passed", "issues": []}
```

## 🔧 Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**
   - Check webhook URL is accessible
   - Verify webhook secret matches
   - Check firewall/security group settings

2. **Authentication Errors**
   - Verify App ID and Installation ID are correct
   - Check private key format (PEM with proper line breaks)
   - Ensure app has required permissions

3. **SSL Certificate Issues**
   - Use valid SSL certificate for webhook URL
   - Test webhook endpoint with curl

### Debug Mode

Enable debug logging:

```python
# In src/github_webhooks.py
webhook_handler.run(debug=True)
```

### Webhook Testing

Test webhook locally:

```bash
curl -X POST http://localhost:5000/github-webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen": "Non-blocking is better than blocking."}'
```

## 📊 Monitoring

### Check App Status

Monitor your GitHub App:

1. **GitHub App Settings**
   - View installation status
   - Check webhook deliveries
   - Monitor API rate limits

2. **Application Logs**
   - Check webhook server logs
   - Monitor SQL analysis results
   - Track error rates

### Metrics

Track important metrics:
- Webhook delivery success rate
- SQL analysis completion time
- User engagement (comments, reactions)
- Pull request check run success rate

## 🔄 Updates & Maintenance

### Updating the App

1. **Update Code**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

2. **Restart Webhook Server**
   ```bash
   # Kill existing process
   pkill -f "python -m src.github_webhooks"
   
   # Start new process
   python -m src.github_webhooks
   ```

3. **Test Changes**
   - Create test events
   - Monitor webhook deliveries
   - Check logs for errors

### Backup Configuration

Regularly backup:
- GitHub App private key
- Environment configuration
- Webhook settings
- Installation mappings

## 🆘 Support

If you encounter issues:

1. **Check Logs**: Review webhook server and application logs
2. **GitHub Docs**: Consult [GitHub Apps documentation](https://docs.github.com/en/developers/apps)
3. **Test Webhooks**: Use GitHub's webhook testing tools
4. **Community**: Open an issue in the project repository

## 📚 Additional Resources

- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)
- [Webhook Events Reference](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [GitHub REST API](https://docs.github.com/en/rest)
- [ngrok Documentation](https://ngrok.com/docs)

---

🎉 **Congratulations!** Your Chat SQL Agent GitHub App is now ready to enhance your SQL development workflow!