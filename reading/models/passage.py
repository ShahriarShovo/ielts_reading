from django.db import models
from .reading_test import ReadingTest

class Passage(models.Model):
    """
    Model representing a reading passage within an IELTS Reading test.
    
    This is the middle-level model in the 3-level hierarchy: Test -> Passage -> Question.
    Each passage belongs to a specific reading test and contains multiple questions.
    
    Key Features:
    - Belongs to a specific reading test
    - Contains the actual reading text for students
    - Ordered sequence within the test
    - Multiple questions per passage
    """
    
    # Foreign key relationship to the parent reading test
    # CASCADE delete means if the test is deleted, all its passages are also deleted
    test = models.ForeignKey(ReadingTest, on_delete=models.CASCADE, related_name='passages')
    
    # Human-readable title for the passage
    title = models.CharField(max_length=255)
    
    # The actual reading text content that students will read
    text = models.TextField()
    
    # Order of this passage within the test (1, 2, 3, etc.)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']  # Order passages by their sequence number

    def __str__(self):
        """String representation for admin panel and debugging"""
        return f"{self.title} (Passage {self.order})"
