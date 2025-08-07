# Deployment Guide

## Overview

This Telegram Photo Editor Bot supports multiple deployment options with both polling and webhook modes for optimal performance across different hosting environments.

## Quick Start Options

### 1. Replit (Development & Testing) ⚡
```bash
# Already configured and running!
# Access at: https://your-repl-name.your-username.repl.co
```

### 2. Docker Local Development 🐳
```bash
# Development with polling
docker-compose up telegram-bot

# Production with webhook
docker-compose --profile webhook up telegram-bot-webhook
```

### 3. Render.com Production 🚀
```bash
# 1. Connect your GitHub repository to Render
# 2. Deploy using render.yaml configuration
# 3. Set environment variables in Render dashboard
```

## Environment Variables

### Required for All Deployments
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
REMOVEBG_API_KEY=your_removebg_api_key
PHOTOROOM_API_KEY=your_photoroom_api_key
```

### Optional Configuration
```env
SESSION_SECRET=your_random_secret_key
PORT=5000
WEBHOOK_MODE=true  # true for webhooks, false for polling
RENDER_EXTERNAL_URL=https://your-app.onrender.com
```

## Deployment Methods

### Docker Deployment 🐳

#### Multi-Stage Production Build
```dockerfile
# Optimized for production with:
# - Multi-stage build for smaller image size
# - Non-root user for security
# - Health checks included
# - Automatic webhook/polling mode switching
```

#### Development vs Production
```bash
# Development (polling mode)
docker run -e WEBHOOK_MODE=false telegram-photo-bot

# Production (webhook mode) 
docker run -e WEBHOOK_MODE=true -e RENDER_EXTERNAL_URL=https://yourdomain.com telegram-photo-bot
```

### Render.com Production Deployment 🌐

#### Automatic Features
- **Auto HTTPS**: SSL certificates managed automatically
- **Health Checks**: Continuous monitoring at `/health`
- **Auto Scaling**: Handle traffic spikes automatically
- **Persistent Storage**: 2GB disk for processed images
- **Multi-Region**: Oregon region for optimal performance

#### Deployment Steps
1. **Connect Repository**: Link your GitHub repo to Render
2. **Configure Environment**: Set all required API keys
3. **Deploy**: render.yaml handles everything automatically
4. **Verify**: Check health endpoint and bot functionality

#### render.yaml Features
```yaml
# Production-optimized configuration:
- Gunicorn with 2 workers
- 120s timeout for large image processing
- Auto-deploy on git push
- Security headers included
- Custom domain support ready
```

### Webhook vs Polling Modes

#### Webhook Mode (Production) 🌐
- **Best for**: Production deployments (Render, Heroku, etc.)
- **Advantages**: Lower latency, better performance, real-time responses
- **Requirements**: Public HTTPS URL, webhook setup
- **Automatic**: Detects WEBHOOK_MODE=true and switches modes

#### Polling Mode (Development) 🔄
- **Best for**: Local development, testing, Replit
- **Advantages**: Simple setup, works behind firewalls
- **Requirements**: Just bot token
- **Default**: Falls back to polling if webhook setup fails

## Monitoring & Health Checks

### Health Endpoints
```bash
# Overall system health
curl https://your-app.com/health

# AI API status only
curl https://your-app.com/api/ai-status

# Bot status (polling mode only)
curl https://your-app.com/api/bot/status
```

### Web Dashboard
- **URL**: https://your-app.com/
- **Features**: Real-time status, AI API monitoring, manual bot controls
- **Updates**: Auto-refresh every 5 seconds

## Security Features

### Docker Security
- Non-root user execution
- Minimal attack surface with slim base image
- Proper file permissions
- Network isolation ready

### Production Security
- HTTPS enforced on Render.com
- Security headers (X-Frame-Options, X-Content-Type-Options)
- Environment variable security
- API key validation

## Performance Optimization

### Image Processing
- Multi-step AI enhancement for large upscaling
- Progressive JPEG output with optimization
- Automatic cleanup of temporary files
- Memory-efficient processing pipeline

### Server Configuration
- Gunicorn with optimized worker count
- Keep-alive connections for better performance
- Request limits to prevent memory issues
- Health checks for reliability

## Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check health endpoint
curl https://your-app.com/health

# Verify environment variables are set
# Check webhook URL is accessible
# Confirm bot token is valid
```

#### Image Processing Failures
```bash
# Check AI API status
curl https://your-app.com/api/ai-status

# Verify API keys in environment
# Check file permissions in uploads/processed directories
```

#### Deployment Failures
```bash
# Docker: Check logs
docker logs telegram-photo-bot

# Render: Check build logs in dashboard
# Verify all environment variables are set
# Confirm repository access
```

### Debug Mode
```bash
# Enable debug logging (development only)
export FLASK_DEBUG=1
export FLASK_ENV=development
```

## Scaling Considerations

### Horizontal Scaling
- **Docker**: Use docker-compose scale
- **Render**: Upgrade to Pro plan for auto-scaling
- **Load Balancing**: Multiple webhook endpoints supported

### Storage Scaling
- **Local**: Regular cleanup of processed/ directory
- **Cloud**: Consider cloud storage integration for large volumes
- **Database**: Add PostgreSQL for user state if needed

## Cost Optimization

### Free Tier Options
- **Render**: 750 hours/month free
- **Replit**: Always-on with Hacker plan
- **Docker**: Self-hosted on any cloud provider

### Paid Scaling
- **Render Standard**: $7/month for production apps
- **AI APIs**: Pay-per-use (Remove.bg: $0.50/image, PhotoRoom: varies)

## Next Steps

1. **Choose Deployment**: Select based on your needs (Replit/Docker/Render)
2. **Set Environment**: Configure all required API keys
3. **Deploy**: Follow platform-specific instructions
4. **Test**: Send photos to bot and verify all features work
5. **Monitor**: Use health endpoints and dashboard for ongoing monitoring

Your bot is production-ready with enterprise-grade features! 🎉