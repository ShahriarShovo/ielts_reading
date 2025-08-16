# 📖 IELTS Reading - Question Management System

A Django-based microservice for managing IELTS Reading tests, passages, and questions. This system provides a comprehensive 3-level hierarchy (Test → Passage → Question) for creating and managing IELTS Reading content. It operates as part of a microservices architecture, communicating with the main Academiq authentication system.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [API Documentation](#api-documentation)
- [Database Models](#database-models)
- [Question Types](#question-types)
- [Microservices Integration](#microservices-integration)
- [Security](#security)
- [Frontend Integration](#frontend-integration)

## 🚀 Overview

IELTS Reading is a specialized microservice designed to handle:

- **Reading Tests**: Complete IELTS Reading test management
- **Passages**: Multiple passages per test with ordering
- **Questions**: 14 different question types with dynamic configuration
- **Secure Storage**: Organization-specific content management
- **Dynamic Configuration**: Question type properties managed from database
- **Media Management**: Image support for questions
- **Microservices Communication**: Secure integration with the main authentication system

## ✨ Features

### 📋 Test Management

- Create, read, update, delete Reading Tests
- Organization-specific test isolation
- Automatic timestamp management

### 📄 Passage Management

- Create, read, update, delete Reading Passages
- Link passages to specific tests
- Order management for passage sequence
- Text content with minimum length validation

### ❓ Question Management

- Create, read, update, delete Reading Questions
- 14 different question types supported
- Dynamic question type configuration
- Options management for multiple choice questions
- Word limit validation
- Image support for questions
- Order management within passages

### 🔧 Dynamic Configuration

- Question type properties managed from database
- Configurable requirements (options, word limits, images)
- Easy addition of new question types
- Active/inactive question type management

### 🔐 Security Features

- JWT token verification through shared authentication service
- Organization-based access control
- API key authentication for microservices
- Secure file upload handling
- Auto-assignment and verification of organization_id

## 🏗️ Architecture

```
IELTS Reading (Port 8002)
├── Test Management
│   ├── ReadingTest CRUD Operations
│   └── Organization-specific isolation
├── Passage Management
│   ├── Passage CRUD Operations
│   └── Test association
├── Question Management
│   ├── Question CRUD Operations
│   ├── 14 Question Types
│   └── Dynamic configuration
├── Question Type Configuration
│   ├── Dynamic properties
│   └── Database-driven configuration
└── Authentication Gateway
    └── Academiq (Port 8000)
```

### Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **Authentication**: Shared JWT verification
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Media Storage**: Local file system with media proxy
- **Communication**: HTTP/REST APIs with API key authentication
- **CORS**: django-cors-headers
- **Frontend**: React.js integration

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip
- Git

### Setup Instructions

1. **Clone the repository**

```bash
git clone <repository-url>
cd ielts_reading
```

2. **Create virtual environment**

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**

```bash
cd core
pip install -r requirements.txt
```

4. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Initialize question types**

```bash
python manage.py init_question_types
```

6. **Create superuser (optional)**

```bash
python manage.py createsuperuser
```

7. **Run the server**

```bash
python manage.py runserver 8002
```

The server will be available at `http://127.0.0.1:8002`

## 📚 API Documentation

### Base URL

```
http://127.0.0.1:8002/api/reading
```

### Authentication

All endpoints require authentication through the shared authentication service. Include the JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Reading Test Endpoints

#### 1. Create Reading Test

```http
POST /api/reading/tests/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "IELTS Academic Reading Test 1"
}
```

**Response:**

```json
{
  "id": 1,
  "organization_id": "1",
  "title": "IELTS Academic Reading Test 1",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 2. Get All Reading Tests

```http
GET /api/reading/tests/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
[
  {
    "id": 1,
    "organization_id": "1",
    "title": "IELTS Academic Reading Test 1",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 3. Update Reading Test

```http
PUT /api/reading/tests/{id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "Updated Test Title"
}
```

#### 4. Delete Reading Test

```http
DELETE /api/reading/tests/{id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

### Passage Endpoints

#### 1. Create Passage

```http
POST /api/reading/passages/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "test": 1,
  "title": "The History of Coffee",
  "text": "Coffee is a brewed drink prepared from roasted coffee beans, the seeds of berries from certain Coffea species. The genus Coffea is native to tropical Africa and Madagascar, the Comoros, Mauritius, and Réunion in the Indian Ocean. Coffee plants are now cultivated in over 70 countries, primarily in the equatorial regions of the Americas, Southeast Asia, the Indian subcontinent, and Africa. The two most commonly grown are C. arabica and C. robusta. Once ripe, coffee berries are picked, processed, and dried. Dried coffee seeds are roasted to varying degrees, depending on the desired flavor. Roasted beans are ground and then brewed with near-boiling water to produce the beverage known as coffee.",
  "order": 1
}
```

**Response:**

```json
{
  "id": 1,
  "test": 1,
  "title": "The History of Coffee",
  "text": "Coffee is a brewed drink prepared from roasted coffee beans...",
  "order": 1
}
```

#### 2. Get All Passages

```http
GET /api/reading/passages/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 3. Update Passage

```http
PUT /api/reading/passages/{id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "test": 1,
  "title": "Updated Passage Title",
  "text": "Updated passage content...",
  "order": 1
}
```

#### 4. Delete Passage

```http
DELETE /api/reading/passages/{id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

### Question Endpoints

#### 1. Create Question

```http
POST /api/reading/questions/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body (Multiple Choice):**

```json
{
  "passage": 1,
  "question_text": "Where did coffee originate according to the passage?",
  "question_type": "MC",
  "options": ["Yemen", "Ethiopia", "Turkey", "Persia"],
  "correct_answer": "Ethiopia",
  "word_limit": 1,
  "order": 1
}
```

**Request Body (True/False/Not Given):**

```json
{
  "passage": 1,
  "question_text": "The first coffeehouse in Europe opened in Venice.",
  "question_type": "TFNG",
  "correct_answer": "True",
  "order": 2
}
```

**Request Body (Short Answer):**

```json
{
  "passage": 1,
  "question_text": "What does the Arabic word 'qahwah' originally refer to?",
  "question_type": "SA",
  "correct_answer": "wine",
  "word_limit": 1,
  "order": 3
}
```

**Response:**

```json
{
  "id": 1,
  "organization_id": "1",
  "passage": 1,
  "question_text": "Where did coffee originate according to the passage?",
  "question_type": "MC",
  "data": {
    "options": ["Yemen", "Ethiopia", "Turkey", "Persia"],
    "correct_answer": "Ethiopia"
  },
  "points": 1,
  "word_limit": 1,
  "explanation": "",
  "image": null,
  "order": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 2. Get All Questions

```http
GET /api/reading/questions/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 3. Update Question

```http
PUT /api/reading/questions/{id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "passage": 1,
  "question_text": "Updated question text",
  "question_type": "MC",
  "options": ["Updated", "Options", "Here"],
  "correct_answer": "Updated",
  "word_limit": 1,
  "order": 1
}
```

#### 4. Delete Question

```http
DELETE /api/reading/questions/{id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

### Question Type Configuration Endpoints

#### 1. Get All Question Types

```http
GET /api/reading/question-types/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response:**

```json
[
  {
    "id": 1,
    "type_code": "MC",
    "display_name": "Multiple Choice",
    "description": "Choose the correct answer from given options",
    "is_active": true,
    "requires_options": true,
    "requires_multiple_answers": false,
    "requires_word_limit": false,
    "requires_image": false,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 2. Create Question Type

```http
POST /api/reading/question-types/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "type_code": "CUSTOM",
  "display_name": "Custom Question Type",
  "description": "A custom question type",
  "requires_options": true,
  "requires_multiple_answers": false,
  "requires_word_limit": true,
  "requires_image": false
}
```

## 🗄️ Database Models

### ReadingTest Model

```python
class ReadingTest(models.Model):
    organization_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255, default='IELTS Academic Reading Test')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
```

### Passage Model

```python
class Passage(models.Model):
    test = models.ForeignKey(ReadingTest, on_delete=models.CASCADE, related_name='passages')
    title = models.CharField(max_length=255)
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']
```

### Question Model

```python
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('MC', 'Multiple Choice'),
        ('TFNG', 'True/False/Not Given'),
        ('YNN', 'Yes/No/Not Given'),
        ('SA', 'Short Answer'),
        ('SC', 'Sentence Completion'),
        ('SUMC', 'Summary Completion'),
        ('NC', 'Note Completion'),
        ('TC', 'Table Completion'),
        ('FCC', 'Flow Chart Completion'),
        ('MF', 'Matching Features'),
        ('MSE', 'Matching Sentence Endings'),
        ('DL', 'Diagram Labeling'),
        ('PFL', 'Pick from List'),
        ('MH', 'Matching Headings'),
    ]

    organization_id = models.CharField(max_length=100)
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    data = models.JSONField(default=dict)
    points = models.PositiveIntegerField(default=1)
    word_limit = models.PositiveIntegerField(default=3, blank=True, null=True)
    explanation = models.TextField(blank=True)
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
```

### QuestionTypeConfig Model

```python
class QuestionTypeConfig(models.Model):
    type_code = models.CharField(max_length=10, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    requires_options = models.BooleanField(default=False)
    requires_multiple_answers = models.BooleanField(default=False)
    requires_word_limit = models.BooleanField(default=False)
    requires_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_name']
```

## ❓ Question Types

The system supports 14 different IELTS Reading question types:

### 1. Multiple Choice (MC)

- **Description**: Choose the correct answer from given options
- **Requires**: Options, Correct Answer
- **Example**: "Where did coffee originate according to the passage?"

### 2. True/False/Not Given (TFNG)

- **Description**: Determine if statement is true, false, or not given
- **Requires**: Correct Answer (True/False/Not Given)
- **Example**: "The first coffeehouse in Europe opened in Venice."

### 3. Yes/No/Not Given (YNN)

- **Description**: Determine if statement agrees with writer's views
- **Requires**: Correct Answer (Yes/No/Not Given)
- **Example**: "Coffee was first cultivated in Yemen in the 15th century."

### 4. Short Answer (SA)

- **Description**: Answer questions with short responses
- **Requires**: Correct Answer, Word Limit
- **Example**: "What does the Arabic word 'qahwah' originally refer to?"

### 5. Sentence Completion (SC)

- **Description**: Complete sentences with words from the passage
- **Requires**: Correct Answer
- **Example**: "The Dutch were the first to transport coffee plants to the New World..."

### 6. Summary Completion (SUMC)

- **Description**: Complete a summary with words from the passage
- **Requires**: Correct Answer, Word Limit
- **Example**: "Complete the summary: Coral reefs support about 4,000 species..."

### 7. Note Completion (NC)

- **Description**: Complete notes with words from the passage
- **Requires**: Correct Answer, Word Limit
- **Example**: "Complete the notes: Coral reefs provide food, protection..."

### 8. Table Completion (TC)

- **Description**: Complete a table with information from the passage
- **Requires**: Correct Answer
- **Example**: "Complete the table: Coral reefs support 4,000 species of fish..."

### 9. Flow Chart Completion (FCC)

- **Description**: Complete a flow chart with words from the passage
- **Requires**: Correct Answer
- **Example**: "Complete the flow chart: Rising temperatures → Coral bleaching..."

### 10. Matching Features (MF)

- **Description**: Match features to items from a list
- **Requires**: Options, Correct Answer
- **Example**: "Match the AI application with its benefit: Early disease detection..."

### 11. Matching Sentence Endings (MSE)

- **Description**: Match sentence beginnings with endings
- **Requires**: Options, Correct Answer
- **Example**: "Complete the sentence: AI algorithms can analyze patterns..."

### 12. Diagram Labeling (DL)

- **Description**: Label parts of a diagram
- **Requires**: Correct Answer
- **Example**: "Label the diagram: AI in healthcare includes machine learning..."

### 13. Pick from List (PFL)

- **Description**: Choose answers from a given list
- **Requires**: Options, Correct Answer
- **Example**: "Choose from the list the main challenge of implementing AI..."

### 14. Matching Headings (MH)

- **Description**: Match paragraph headings to paragraphs
- **Requires**: Options, Correct Answer
- **Example**: "Which heading best describes the importance of coral reefs?"

## 🔗 Microservices Integration

### Authentication Flow

1. **Token Verification**: All requests are verified through the shared authentication service
2. **Organization Assignment**: Organization ID is automatically assigned from JWT token
3. **Permission Checking**: Access is restricted to organization-specific data
4. **API Key Security**: Cross-project communication uses secure API keys

### Communication with Academiq

```python
# Authentication verification
POST http://127.0.0.1:8000/api/user/auth/verify-token/
Authorization: Bearer <jwt_token>

# Response
{
  "verified": true,
  "user_id": 2,
  "organization_id": 1,
  "user_email": "ielts@org.com",
  "user_type": "organization",
  "message": "Token verified successfully"
}
```

## 🔐 Security

### Organization-Based Data Isolation

- **Auto-Assignment**: Organization ID is automatically assigned from JWT token
- **Verification**: Client-sent organization ID is verified against token
- **Isolation**: All data is filtered by organization ID
- **Prevention**: Cross-organization access is blocked

### API Security

- **JWT Authentication**: All endpoints require valid JWT tokens
- **API Key Protection**: Cross-project communication uses secure keys
- **CORS Configuration**: Proper CORS headers for frontend integration
- **Input Validation**: Comprehensive validation for all inputs

### Security Implementation

```python
# Auto-assignment and verification
def auto_assign_organization_id(request, data):
    """Auto-assign organization_id from JWT token"""
    data['organization_id'] = getattr(request, 'organization_id', None)
    return data

def verify_organization_id(request, data):
    """Verify organization_id matches JWT token"""
    token_org_id = getattr(request, 'organization_id', None)
    data_org_id = data.get('organization_id')

    if token_org_id != data_org_id:
        raise PermissionDenied("Organization ID mismatch")
```

## 🎨 Frontend Integration

### React Component

The system includes a comprehensive React component (`IELTSReadingQuestionManager.js`) that provides:

- **Tabbed Interface**: Tests, Passages, and Questions management
- **Form Validation**: Client-side validation for all inputs
- **Dynamic Options**: Auto-management of options for multiple choice questions
- **Real-time Updates**: Automatic data refresh after operations
- **Error Handling**: Comprehensive error messages and validation

### Key Features

- **Auto-Initialization**: Questions start with 4 empty options for MC types
- **Smart Validation**: Prevents submission without required options
- **Type Switching**: Automatically manages options when changing question types
- **User Guidance**: Clear instructions and helpful messages

### Usage Example

```javascript
// Initialize question form with options
const initializeQuestionForm = () => {
  setQuestionForm({
    passage: "",
    question_text: "",
    question_type: "MC",
    options: ["", "", "", ""], // Auto-add 4 empty options
    correct_answer: "",
    word_limit: 3,
    order: 1,
  });
};

// Handle question type changes
const handleQuestionTypeChange = (newType) => {
  const requiresOptions = ["MC", "MH", "MF", "MSE", "PFL"];
  if (requiresOptions.includes(newType)) {
    // Ensure at least 4 options for MC types
    if (questionForm.options.length < 4) {
      setQuestionForm((prev) => ({
        ...prev,
        question_type: newType,
        options: [...prev.options, ...Array(4 - prev.options.length).fill("")],
      }));
    }
  }
};
```

## 🚀 Getting Started

### Quick Start Guide

1. **Start the Academiq server** (Port 8000)
2. **Start the IELTS Reading server** (Port 8002)
3. **Initialize question types**: `python manage.py init_question_types`
4. **Create a test**: Use the API or frontend interface
5. **Add passages**: Link passages to your test
6. **Create questions**: Add questions with appropriate types and options

### Example Workflow

1. **Create Test**: "IELTS Academic Reading Test 1"
2. **Add Passage**: "The History of Coffee" with content
3. **Add Questions**: Multiple choice, true/false, short answer questions
4. **Configure Options**: Set up options for multiple choice questions
5. **Test Integration**: Verify frontend-backend communication

## 📝 Notes

- **Organization ID**: Automatically managed from JWT tokens
- **Question Types**: 14 standard IELTS question types supported
- **Validation**: Comprehensive validation for all question types
- **Options**: Required for multiple choice questions (MC, MH, MF, MSE, PFL)
- **Word Limits**: Important for completion questions
- **Images**: Supported for questions that require visual content

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive validation for new question types
3. Update documentation for any new features
4. Test thoroughly with the frontend integration
5. Ensure organization-based security is maintained

## 📞 Support

For technical support or questions about the IELTS Reading system, please refer to the main Academiq documentation or contact the development team.
