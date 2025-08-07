# Overview

A comprehensive Telegram bot application that provides professional AI-powered photo editing capabilities with external API integrations. The system features a Flask web dashboard for monitoring and configuration, and a Telegram bot that processes user images with advanced editing features including resizing, cropping, AI background removal (Remove.bg), AI background generation (PhotoRoom), and multi-resolution quality enhancement. The application supports multiple deployment modes including Replit development, Docker containerization with multi-stage builds, and production deployment on Render.com with both webhook and polling support for maximum flexibility.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Web Dashboard**: Flask-based web interface using Bootstrap 5 with dark theme
- **Real-time Updates**: JavaScript polling mechanism for live bot status updates
- **Responsive Design**: Mobile-friendly interface with Bootstrap grid system and custom CSS animations
- **Template Engine**: Jinja2 templating with base template inheritance

## Backend Architecture
- **Flask Application**: Lightweight WSGI web framework serving the dashboard with API endpoints
- **Simple Telegram Bot**: Custom asynchronous bot implementation using direct Telegram API calls
- **Threading Model**: Bot runs in separate thread with asyncio polling for concurrent operations
- **Image Processing**: Multi-tier approach with PIL (Pillow) for local operations and AI APIs for advanced features
- **State Management**: In-memory user state tracking for multi-step bot interactions and photo handling
- **AI API Integration**: Remove.bg for professional background removal, PhotoRoom for AI background generation

## Bot Integration
- **Command Handlers**: Structured command processing (/start, /help, /status) with Markdown formatting
- **Message Processing**: Advanced photo message handling with file download and temporary storage
- **Callback Management**: Multi-level interactive menus for editing options and resolution selection
- **Error Handling**: Comprehensive exception handling with user-friendly error messages
- **API Status**: Real-time monitoring of external AI service availability

## File Management
- **Temporary Storage**: Local file system for processed images with unique filename generation
- **Image Formats**: JPEG output with quality optimization and format conversion
- **Cleanup Strategy**: Organized directory structure for processed files

## Configuration Management
- **Environment Variables**: Bot token and session secrets via environment configuration
- **Logging**: Centralized logging configuration across all components
- **Development Mode**: Flask debug mode for development environment

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web framework for dashboard interface and API endpoints
- **Requests**: HTTP client for external API communication and Telegram API
- **Pillow (PIL)**: Advanced image processing and manipulation library
- **Gunicorn**: WSGI HTTP server for production deployment

## AI Service Dependencies
- **Remove.bg API**: Professional AI-powered background removal service
- **PhotoRoom API**: AI background generation and replacement service
- **Custom AI Processor**: Local fallback implementations for offline functionality

## Frontend Dependencies
- **Bootstrap 5**: CSS framework with Replit dark theme support
- **Bootstrap Icons**: Icon library for UI elements
- **Custom CSS**: Enhanced styling with animations and responsive design
- **Real-time Updates**: JavaScript polling for live status monitoring

## Infrastructure Requirements
- **Telegram Bot API**: Requires valid bot token from BotFather
- **File System**: Organized directory structure for uploads and processed images
- **Network Access**: Internet connectivity for Telegram API and AI service communication
- **Environment Variables**: Secure configuration for API keys and tokens

## Deployment Support
- **Docker**: Multi-stage production builds with security hardening, non-root user execution, and automatic webhook/polling mode switching
- **Render.com**: Enterprise-grade production deployment with auto-scaling, HTTPS, health monitoring, and 2GB persistent storage
- **Webhook Server**: Dedicated production webhook server (webhook_server.py) for high-performance real-time processing
- **Port Configuration**: Dynamic port binding with environment variable support for cloud hosting platforms
- **Multi-Mode Support**: Automatic detection and switching between webhook (production) and polling (development) modes

## Development Tools
- **Werkzeug**: WSGI utilities and development server with auto-reload
- **Asyncio**: Asynchronous programming for bot polling and concurrent operations
- **UUID**: Unique identifier generation for processed files and session management
- **Logging**: Comprehensive logging system for debugging and monitoring