from django.urls import path
from .views import (
    # REST API Views
    ReadingQuestionView,
    PassageView,
    ReadingTestView,
    QuestionTypeConfigView,
)

app_name = 'reading'

urlpatterns = [
    # REST API URLs for Reading Tests
    path('tests/', ReadingTestView.as_view(), name='api_tests'),
    path('tests/<int:pk>/', ReadingTestView.as_view(), name='api_test_detail'),
    
    # REST API URLs for Reading Passages
    path('passages/', PassageView.as_view(), name='api_passages'),
    path('passages/<int:pk>/', PassageView.as_view(), name='api_passage_detail'),
    
    # REST API URLs for Reading Questions
    path('questions/', ReadingQuestionView.as_view(), name='api_questions'),
    path('questions/<int:pk>/', ReadingQuestionView.as_view(), name='api_question_detail'),
    
    # REST API URLs for Question Type Configuration
    path('question-types/', QuestionTypeConfigView.as_view(), name='api_question_types'),
    path('question-types/<int:pk>/', QuestionTypeConfigView.as_view(), name='api_question_type_detail'),
]
