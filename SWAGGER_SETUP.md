# IELTS Reading Project - Swagger API Documentation

## ✅ Installation Complete!

Swagger has been successfully configured for the IELTS Reading project.

## 🚀 How to Access Swagger

### 1. Install Dependencies

```bash
cd ielts_reading
pip install -r requirements.txt
```

### 2. Run Server

```bash
python manage.py runserver 8002
```

### 3. Access Swagger UI

Open your browser and go to:

- **Swagger UI**: http://127.0.0.1:8002/swagger/
- **ReDoc**: http://127.0.0.1:8002/redoc/
- **JSON Schema**: http://127.0.0.1:8002/swagger.json

## 📋 Available APIs

### Reading APIs

- `/api/reading/` - Reading passages, questions, and answers
  - `GET /api/reading/random-questions/` - Get random reading questions
  - `POST /api/reading/save-answers/` - Save student reading answers
  - `POST /api/reading/submit-exam/` - Submit reading exam
  - `GET /api/reading/passages/` - Get reading passages
  - `GET /api/reading/questions/` - Get questions for passages

## 🔐 Authentication

Most APIs require JWT authentication:

1. Get token from Academiq project login API
2. Click "Authorize" button in Swagger UI
3. Enter: `Bearer <your-jwt-token>`

## 🎯 Features

- **Interactive Testing**: Test APIs directly from browser
- **Auto-generated Documentation**: All endpoints documented
- **Request/Response Examples**: See data formats
- **Authentication Support**: JWT token integration
- **Search & Filter**: Find APIs quickly

## 📝 Reading API Examples

### Get Random Questions

```json
GET /api/reading/random-questions/
Response:
{
  "passage": {
    "id": 1,
    "title": "Sample Passage",
    "content": "Reading passage content...",
    "image": "/media/diagrams/diagram.jpg"
  },
  "questions": [
    {
      "id": 1,
      "question_text": "What is the main idea?",
      "question_type": "multiple_choice",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A"
    }
  ]
}
```

### Save Reading Answers

```json
POST /api/reading/save-answers/
{
  "student_id": 1,
  "session_id": "abc123",
  "answers": [
    {
      "question_id": 1,
      "student_answer": "A"
    }
  ]
}
```

## 🎉 Ready to Use!

Your IELTS Reading Swagger documentation is now ready. You can track all APIs, test them, and see their documentation in a beautiful interface!
