# Smart Energy Management System (HEMS) Backend

A FastAPI backend for real-time energy monitoring with AI integration.

## Features

- Real-time power consumption tracking
- IoT sensor data ingestion
- AI-powered energy predictions
- User and device management
- Environment monitoring
- Flutter-compatible REST API

## Setup

1. **Clone and install dependencies:**
```bash
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your MongoDB and AI Agent details


uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

