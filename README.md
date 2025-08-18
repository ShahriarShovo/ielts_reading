# 📖 IELTS Reading - Question Management System

A Django-based microservice for managing IELTS Reading tests, passages, and questions. This system provides a comprehensive 4-level hierarchy (Test → Passage → Question Type → Individual Questions) for creating and managing IELTS Reading content. It operates as part of a microservices architecture, communicating with the main Academiq authentication system.

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

- **Reading Tests**: Complete IELTS Reading test management with UUID-based identifiers
- **Passages**: Multiple passages per test with ordering and instruction templates
- **Question Types**: 14 different question types with dynamic instruction templates and JSON question data
- **Individual Questions**: Questions stored as JSON within question types for flexibility
- **Secure Storage**: Organization-specific content management
- **Dynamic Instructions**: Template-based instructions with dynamic placeholders
- **Media Management**: Image support for questions
- **Microservices Communication**: Secure integration with the main authentication system

## ✨ Features

### 📋 Test Management

- Create, read, update, delete Reading Tests with UUID identifiers
- Organization-specific test isolation
- Source tracking (Cambridge, Custom, etc.)
- Automatic timestamp management

### 📄 Passage Management

- Create, read, update, delete Reading Passages with UUID identifiers
- Link passages to specific tests
- IELTS-style instruction templates with dynamic placeholders
- Order management for passage sequence
- Text content with minimum length validation

### ❓ Question Type Management

- Create, read, update, delete Question Types with UUID identifiers
- 14 different question types supported
- Dynamic instruction templates with placeholders ({start}, {end}, {passage_number})
- Expected vs actual question count for flexibility
- JSON storage for individual questions data
- Order management within passages

### 🔧 Individual Question Management

- Questions stored as JSON within QuestionType models
- Support for all standard IELTS question types
- Options management for multiple choice questions
- Word limit validation
- Image support for questions
- Sequential numbering within question types

### 🔐 Security Features

- JWT token verification through shared authentication service
- Organization-based access control
- API key authentication for microservices
- Secure file upload handling
- Auto-assignment and verification of organization_id

## 🏗️ Architecture

```
IELTS Reading (Port 8002)
├── Test Management (UUID-based)
│   ├── ReadingTest CRUD Operations
│   ├── Source tracking (Cambridge, Custom)
│   └── Organization-specific isolation
├── Passage Management (UUID-based)
│   ├── Passage CRUD Operations
│   ├── Test association
│   ├── Instruction templates
│   └── Dynamic placeholders
├── Question Type Management (UUID-based)
│   ├── QuestionType CRUD Operations
│   ├── 14 Question Types
│   ├── Instruction templates
│   └── JSON question data
├── Individual Question Management
│   ├── JSON-based storage
│   ├── Question validation
│   └── Options management
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

### Reading Test Endpoints (UUID-based)

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
  "test_name": "Cambridge IELTS 18 Academic",
  "source": "Cambridge IELTS 18"
}
```

**Response:**

```json
{
  "message": "Reading test created successfully",
  "test": {
    "test_id": "550e8400-e29b-41d4-a716-446655440000",
    "test_name": "Cambridge IELTS 18 Academic",
    "source": "Cambridge IELTS 18",
    "organization_id": "1",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "passage_count": 0,
    "total_question_count": 0
  }
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
{
  "message": "Reading tests retrieved successfully",
  "tests": [
    {
      "test_id": "550e8400-e29b-41d4-a716-446655440000",
      "test_name": "Cambridge IELTS 18 Academic",
      "source": "Cambridge IELTS 18",
      "organization_id": "1",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "passage_count": 3,
      "total_question_count": 40
    }
  ],
  "count": 1
}
```

#### 3. Get Specific Reading Test

```http
GET /api/reading/tests/{test_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 4. Update Reading Test

```http
PUT /api/reading/tests/{test_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "test_name": "Updated Test Name",
  "source": "Updated Source"
}
```

#### 5. Delete Reading Test

```http
DELETE /api/reading/tests/{test_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

### Passage Endpoints (UUID-based)

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
  "test": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The History of Coffee",
  "instruction": "You should spend about 20 minutes on Questions 1-13, which are based on Reading Passage 1 below.",
  "text": "Coffee is a brewed drink prepared from roasted coffee beans, the seeds of berries from certain Coffea species. The genus Coffea is native to tropical Africa and Madagascar, the Comoros, Mauritius, and Réunion in the Indian Ocean. Coffee plants are now cultivated in over 70 countries, primarily in the equatorial regions of the Americas, Southeast Asia, the Indian subcontinent, and Africa. The two most commonly grown are C. arabica and C. robusta. Once ripe, coffee berries are picked, processed, and dried. Dried coffee seeds are roasted to varying degrees, depending on the desired flavor. Roasted beans are ground and then brewed with near-boiling water to produce the beverage known as coffee.",
  "order": 1
}
```

**Response:**

```json
{
  "message": "Passage created successfully",
  "passage": {
    "passage_id": "550e8400-e29b-41d4-a716-446655440001",
    "test": "550e8400-e29b-41d4-a716-446655440000",
    "title": "The History of Coffee",
    "instruction": "You should spend about 20 minutes on Questions 1-13, which are based on Reading Passage 1 below.",
    "text": "Coffee is a brewed drink prepared from roasted coffee beans...",
    "order": 1,
    "question_type_count": 0,
    "total_question_count": 0,
    "question_range": "1-0"
  }
}
```

#### 2. Get All Passages for a Test

```http
GET /api/reading/passages/?test_id={test_id}
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 3. Get Specific Passage

```http
GET /api/reading/passages/{passage_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 4. Update Passage

```http
PUT /api/reading/passages/{passage_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "Updated Passage Title",
  "instruction": "Updated instruction text",
  "text": "Updated passage content...",
  "order": 1
}
```

#### 5. Delete Passage

```http
DELETE /api/reading/passages/{passage_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

### Question Type Endpoints (UUID-based)

#### 1. Create Question Type

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
  "passage": "550e8400-e29b-41d4-a716-446655440001",
  "type": "Multiple Choice Questions (MCQ)",
  "instruction_template": "Questions {start}-{end}\nChoose the correct letter A, B, C or D.",
  "expected_range": "1-7",
  "actual_count": 7,
  "questions_data": [
    {
      "number": 1,
      "text": "Where was coffee first discovered?",
      "options": ["A. Brazil", "B. Ethiopia", "C. Yemen", "D. India"],
      "answer": "B"
    },
    {
      "number": 2,
      "text": "Which country popularized coffee in Europe?",
      "options": ["A. France", "B. Italy", "C. England", "D. Germany"],
      "answer": "B"
    }
  ],
  "order": 1
}
```

**Response:**

```json
{
  "message": "Question type created successfully",
  "question_type": {
    "question_type_id": "550e8400-e29b-41d4-a716-446655440002",
    "passage": "550e8400-e29b-41d4-a716-446655440001",
    "type": "Multiple Choice Questions (MCQ)",
    "instruction_template": "Questions {start}-{end}\nChoose the correct letter A, B, C or D.",
    "expected_range": "1-7",
    "actual_count": 2,
    "questions_data": [...],
    "order": 1,
    "processed_instruction": "Questions 1-2\nChoose the correct letter A, B, C or D.",
    "question_range": "1-2",
    "question_count": 2
  }
}
```

#### 2. Get All Question Types for a Passage

```http
GET /api/reading/question-types/?passage_id={passage_id}
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 3. Get Specific Question Type

```http
GET /api/reading/question-types/{question_type_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

#### 4. Update Question Type

```http
PUT /api/reading/question-types/{question_type_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "type": "Updated Question Type",
  "instruction_template": "Updated instruction template with {start} and {end} placeholders",
  "expected_range": "1-5",
  "questions_data": [
    {
      "number": 1,
      "text": "Updated question text",
      "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
      "answer": "A"
    }
  ],
  "order": 1
}
```

#### 5. Delete Question Type

```http
DELETE /api/reading/question-types/{question_type_id}/
```

**Headers:**

```
Authorization: Bearer <jwt_token>
```

### Legacy Question Endpoints (for backward compatibility)

#### 1. Create Question (Legacy)

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

## 🗄️ Database Models

### ReadingTest Model (Updated)

```python
class ReadingTest(models.Model):
    test_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_name = models.CharField(max_length=255, default='IELTS Academic Reading Test')
    source = models.CharField(max_length=255, default='Custom Test')
    organization_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'reading_test'
        verbose_name = 'Reading Test'
        verbose_name_plural = 'Reading Tests'
```

### Passage Model (Updated)

```python
class Passage(models.Model):
    passage_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(ReadingTest, on_delete=models.CASCADE, related_name='passages')
    title = models.CharField(max_length=255, blank=True, null=True)
    instruction = models.TextField()
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']
        db_table = 'reading_passage'
        verbose_name = 'Reading Passage'
        verbose_name_plural = 'Reading Passages'
```

### QuestionType Model (New)

```python
class QuestionType(models.Model):
    question_type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE, related_name='questions')
    type = models.CharField(max_length=100)
    instruction_template = models.TextField()
    expected_range = models.CharField(max_length=20)
    actual_count = models.PositiveIntegerField(default=0)
    questions_data = models.JSONField(default=list)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']
        db_table = 'reading_question_type'
        verbose_name = 'Question Type'
        verbose_name_plural = 'Question Types'
```

### Question Model (Updated for Individual Questions)

```python
class Question(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, related_name='individual_questions')
    question_text = models.TextField()
    number = models.PositiveIntegerField()
    answer = models.CharField(max_length=255)
    options = models.JSONField(default=list, blank=True)
    word_limit = models.PositiveIntegerField(default=1, blank=True, null=True)
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True)
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        db_table = 'reading_question'
        verbose_name = 'Individual Question'
        verbose_name_plural = 'Individual Questions'
        unique_together = ['question_type', 'number']
```

## ❓ Question Types

The system supports 14 different IELTS Reading question types with dynamic instruction templates:

### 1. Multiple Choice Questions (MCQ)

- **Description**: Choose the correct answer from given options
- **Instruction Template**: "Questions {start}-{end}\nChoose the correct letter A, B, C or D."
- **Requires**: Options, Correct Answer
- **Example**: "Where was coffee first discovered?"

### 2. True/False/Not Given (TFNG)

- **Description**: Determine if statement is true, false, or not given
- **Instruction Template**: "Questions {start}-{end}\nDo the following statements agree with the information given in Reading Passage {passage_number}?"
- **Requires**: Correct Answer (True/False/Not Given)
- **Example**: "The first coffeehouse in Europe opened in Venice."

### 3. Yes/No/Not Given (YNN)

- **Description**: Determine if statement agrees with writer's views
- **Instruction Template**: "Questions {start}-{end}\nDo the following statements agree with the views of the writer in Reading Passage {passage_number}?"
- **Requires**: Correct Answer (Yes/No/Not Given)
- **Example**: "Coffee was first cultivated in Yemen in the 15th century."

### 4. Short Answer Questions

- **Description**: Answer questions with short responses
- **Instruction Template**: "Questions {start}-{end}\nAnswer the questions below using NO MORE THAN THREE WORDS from the passage for each answer."
- **Requires**: Correct Answer, Word Limit
- **Example**: "What does the Arabic word 'qahwah' originally refer to?"

### 5. Sentence Completion

- **Description**: Complete sentences with words from the passage
- **Instruction Template**: "Questions {start}-{end}\nComplete the sentences below using NO MORE THAN TWO WORDS from the passage for each answer."
- **Requires**: Correct Answer
- **Example**: "The Dutch were the first to transport coffee plants to the New World..."

### 6. Summary Completion

- **Description**: Complete a summary with words from the passage
- **Instruction Template**: "Questions {start}-{end}\nComplete the summary using the list of words, A-G, below."
- **Requires**: Correct Answer, Word Limit
- **Example**: "Complete the summary: Coral reefs support about 4,000 species..."

### 7. Note Completion

- **Description**: Complete notes with words from the passage
- **Instruction Template**: "Questions {start}-{end}\nComplete the notes below using NO MORE THAN TWO WORDS from the passage for each answer."
- **Requires**: Correct Answer, Word Limit
- **Example**: "Complete the notes: Coral reefs provide food, protection..."

### 8. Table Completion

- **Description**: Complete a table with information from the passage
- **Instruction Template**: "Questions {start}-{end}\nComplete the table below using NO MORE THAN TWO WORDS from the passage for each answer."
- **Requires**: Correct Answer
- **Example**: "Complete the table: Coral reefs support 4,000 species of fish..."

### 9. Flow Chart Completion

- **Description**: Complete a flow chart with words from the passage
- **Instruction Template**: "Questions {start}-{end}\nComplete the flow chart below using NO MORE THAN TWO WORDS from the passage for each answer."
- **Requires**: Correct Answer
- **Example**: "Complete the flow chart: Rising temperatures → Coral bleaching..."

### 10. Matching Features

- **Description**: Match features to items from a list
- **Instruction Template**: "Questions {start}-{end}\nLook at the following statements and the list of people below. Match each statement with the correct person, A-E."
- **Requires**: Options, Correct Answer
- **Example**: "Match the AI application with its benefit: Early disease detection..."

### 11. Matching Sentence Endings

- **Description**: Match sentence beginnings with endings
- **Instruction Template**: "Questions {start}-{end}\nComplete each sentence with the correct ending, A-G, below."
- **Requires**: Options, Correct Answer
- **Example**: "Complete the sentence: AI algorithms can analyze patterns..."

### 12. Diagram Labeling

- **Description**: Label parts of a diagram
- **Instruction Template**: "Questions {start}-{end}\nLabel the diagram below using NO MORE THAN TWO WORDS from the passage for each answer."
- **Requires**: Correct Answer
- **Example**: "Label the diagram: AI in healthcare includes machine learning..."

### 13. Pick from List

- **Description**: Choose answers from a given list
- **Instruction Template**: "Questions {start}-{end}\nChoose the correct letter, A, B, C or D."
- **Requires**: Options, Correct Answer
- **Example**: "Choose from the list the main challenge of implementing AI..."

### 14. Matching Headings

- **Description**: Match paragraph headings to paragraphs
- **Instruction Template**: "Questions {start}-{end}\nChoose the correct heading for each paragraph from the list of headings below."
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
5. **Add passages**: Link passages to your test with instruction templates
6. **Create question types**: Add question types with dynamic instruction templates
7. **Add individual questions**: Store questions as JSON within question types

### Example Workflow

1. **Create Test**: "Cambridge IELTS 18 Academic" with source "Cambridge IELTS 18"
2. **Add Passage**: "The History of Coffee" with instruction template
3. **Add Question Type**: "Multiple Choice Questions (MCQ)" with instruction template
4. **Add Questions**: Individual questions stored as JSON within the question type
5. **Test Integration**: Verify frontend-backend communication

## 📝 Notes

- **UUID Identifiers**: All new models use UUID-based primary keys for security
- **Instruction Templates**: Dynamic placeholders ({start}, {end}, {passage_number}) for automatic range calculation
- **JSON Question Data**: Individual questions stored as JSON for flexibility
- **Organization ID**: Automatically managed from JWT tokens
- **Question Types**: 14 standard IELTS question types supported with templates
- **Validation**: Comprehensive validation for all question types and instruction templates
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
