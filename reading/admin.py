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
    # Updated list_display to use order_number instead of order
    list_display = ['question_text', 'passage', 'question_type', 'points', 'order_number', 'question_range']
    list_filter = ['question_type', 'passage__test']
    search_fields = ['question_text', 'passage__title']
    # Updated ordering to use order_number instead of order
    ordering = ['passage', 'order_number']
    
    # Updated fieldsets to include new IELTS instruction system fields
    fieldsets = (
        ('Basic Information', {
            'fields': ('passage', 'question_text', 'question_type', 'custom_question_type', 'order_number')
        }),
        ('IELTS Instruction System', {
            'fields': ('question_range', 'instruction', 'answer_format'),
            'classes': ('collapse',),
            'description': 'IELTS-standard instruction and answer format fields'
        }),
        ('Answer Configuration', {
            'fields': ('options', 'correct_answer', 'correct_answers', 'points', 'word_limit')
        }),
        ('Additional Data', {
            'fields': ('data', 'explanation', 'image'),
            'classes': ('collapse',)
        }),
    )
    
    # Add readonly fields for auto-calculated values
    readonly_fields = ['question_range']
    
    # Add help text for the new fields
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['question_range'].help_text = "Auto-calculated range like 'Questions 1-7'"
        form.base_fields['instruction'].help_text = "IELTS instruction text for this question type"
        form.base_fields['answer_format'].help_text = "Format instructions for how to answer"
        form.base_fields['order_number'].help_text = "Sequential order across all question types (1,2,3,4,5...)"
        return form

@admin.register(QuestionTypeConfig)
class QuestionTypeConfigAdmin(admin.ModelAdmin):
    # Updated list_display to include new template fields
    list_display = ['type_code', 'display_name', 'is_active', 'requires_options', 'requires_word_limit']
    list_filter = ['is_active', 'requires_options', 'requires_multiple_answers', 'requires_word_limit', 'requires_image']
    search_fields = ['type_code', 'display_name', 'description']
    ordering = ['display_name']
    
    # Updated fieldsets to include new template fields
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('type_code', 'display_name', 'description', 'is_active')
        }),
        ('Field Requirements', {
            'fields': ('requires_options', 'requires_multiple_answers', 'requires_word_limit', 'requires_image'),
            'description': 'Configuration flags for field requirements'
        }),
        ('IELTS Template System', {
            'fields': ('default_instruction', 'default_answer_format', 'template_examples', 'word_limit_rules'),
            'classes': ('collapse',),
            'description': 'IELTS instruction templates and configuration'
        }),
    )
    
    # Add help text for the new fields
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['default_instruction'].help_text = "Default IELTS instruction text with {question_range} placeholder"
        form.base_fields['default_answer_format'].help_text = "Default answer format with {question_range} placeholder"
        form.base_fields['template_examples'].help_text = "JSON array of template examples for frontend integration"
        form.base_fields['word_limit_rules'].help_text = "Word limit rules and configurations in JSON format"
        return form
