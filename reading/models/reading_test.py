from django.db import models

class ReadingTest(models.Model):
    """
    Model representing a complete IELTS Reading test.
    
    This is the top-level model in the 3-level hierarchy: Test -> Passage -> Question.
    Each reading test contains multiple passages, and each passage contains multiple questions.
    
    Key Features:
    - Organization-based data isolation
    - Multiple passages per test
    - Timestamp tracking for creation and updates
    - Hierarchical relationship with passages
    """
    
    # Links this test to a specific organization for data isolation
    organization_id = models.CharField(max_length=100)
    
    # Human-readable title for the reading test
    title = models.CharField(max_length=255, default='IELTS Academic Reading Test')
    
    # Timestamp when this test was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Timestamp when this test was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Most recent tests first

    def __str__(self):
        """String representation for admin panel and debugging"""
        return f"{self.title} (Org: {self.organization_id})"
