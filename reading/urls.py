from django.urls import path
from .views import PassageView, ReadingTestView, QuestionTypeView
from .views.question_count_view import QuestionCountView
from .views.get_random_questions import RandomQuestionsView
from .views.student_answer_views import SubmitStudentAnswersView
from .views.answer_comparison_views import (
    CompareSubmissionView,
    GetComparisonSummaryView,
    BatchCompareSubmissionsView
)

# URL patterns for the reading app
# Base URL: /api/reading/
# 
# Available endpoints:
# 
# Reading Tests:
# - GET    /api/reading/tests/                    - List all tests
# - POST   /api/reading/tests/                    - Create new test
# - GET    /api/reading/tests/{test_id}/          - Get specific test
# - PUT    /api/reading/tests/{test_id}/          - Update test
# - DELETE /api/reading/tests/{test_id}/          - Delete test
# 
# Passages:
# - GET    /api/reading/passages/                 - List all passages
# - POST   /api/reading/passages/                 - Create passage
# - GET    /api/reading/passages/{passage_id}/    - Get specific passage
# - PUT    /api/reading/passages/{passage_id}/    - Update passage
# - DELETE /api/reading/passages/{passage_id}/    - Delete passage
# 
# Question Types:
# - GET    /api/reading/question-types/           - List all question types
# - POST   /api/reading/question-types/          - Create question type
# - GET    /api/reading/question-types/{id}/      - Get specific question type
# - PUT    /api/reading/question-types/{id}/      - Update question type
# - DELETE /api/reading/question-types/{id}/      - Delete question type
# 
# Query Parameters:
# - organization_id: Filter by organization
# - test_id: Filter by test ID
# - passage_id: Filter by passage ID
# - type: Filter by question type

urlpatterns = [
    # Reading Test endpoints
    path('tests/', ReadingTestView.as_view(), name='reading-test-list'),
    path('tests/<uuid:test_id>/', ReadingTestView.as_view(), name='reading-test-detail'),
    
    # Passage endpoints
    path('passages/', PassageView.as_view(), name='passage-list'),
    path('passages/<uuid:passage_id>/', PassageView.as_view(), name='passage-detail'),
    
    # Question Type endpoints
    path('question-types/', QuestionTypeView.as_view(), name='question-type-list'),
    path('question-types/<uuid:question_type_id>/', QuestionTypeView.as_view(), name='question-type-detail'),
    
    # Question Count endpoint
    path('question-count/', QuestionCountView.as_view(), name='question-count'),
    
    # Random questions endpoint for student exams
    path('random-questions/', RandomQuestionsView.as_view(), name='random-questions'),
    
    # Student Answer Submission API (called by Academiq)
    path('submit-answers/', SubmitStudentAnswersView.as_view(), name='submit-answers'),
    
    # Answer Comparison APIs
    path('compare-submission/', CompareSubmissionView.as_view(), name='compare-submission'),
    path('comparison-summary/<str:submit_id>/', GetComparisonSummaryView.as_view(), name='comparison-summary'),
    path('batch-compare/', BatchCompareSubmissionsView.as_view(), name='batch-compare'),
]