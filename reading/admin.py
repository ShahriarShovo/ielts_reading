from django.contrib import admin
from .models import ReadingTest, Passage, Question, QuestionTypeConfig

# Register your models here.

@admin.register(ReadingTest)
class ReadingTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title']
    list_filter = ['created_at']

@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    list_display = ['title', 'test', 'order']
    list_filter = ['test']
    search_fields = ['title', 'text']
    ordering = ['test', 'order']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'passage', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'passage__test']
    search_fields = ['question_text', 'passage__title']
    ordering = ['passage', 'order']
    fieldsets = (
        ('Basic Information', {
            'fields': ('passage', 'question_text', 'question_type', 'custom_question_type', 'order')
        }),
        ('Answer Configuration', {
            'fields': ('options', 'correct_answer', 'correct_answers', 'points', 'word_limit')
        }),
        ('Additional Data', {
            'fields': ('data', 'explanation', 'image'),
            'classes': ('collapse',)
        }),
    )

@admin.register(QuestionTypeConfig)
class QuestionTypeConfigAdmin(admin.ModelAdmin):
    list_display = ['type_code', 'display_name', 'is_active', 'requires_options', 'requires_word_limit']
    list_filter = ['is_active', 'requires_options', 'requires_multiple_answers', 'requires_word_limit', 'requires_image']
    search_fields = ['type_code', 'display_name', 'description']
    ordering = ['display_name']
