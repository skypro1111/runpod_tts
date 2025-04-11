# TTS Service API

A FastAPI-based Text-to-Speech service with authentication.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access:
- Interactive API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

## Authentication

The API uses JWT tokens for authentication. To use protected endpoints:

1. Register a new user at `/api/v1/auth/register`
2. Get an access token at `/api/v1/auth/login/access-token`
3. Use the token in the Authorization header: `Bearer <token>`

Default superuser credentials:
- Email: admin@example.com
- Password: admin