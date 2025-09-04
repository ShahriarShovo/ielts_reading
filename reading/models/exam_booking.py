# =============================================================================
# EXAM BOOKING MODEL
# =============================================================================
# This model represents a student's booking for an IELTS exam.
# It tracks payment status, module completion, and implements
# the sequential module unlocking system for exam progression.
# =============================================================================

from django.db import models
from django.utils import timezone

class ExamBooking(models.Model):
    """
    ExamBooking: Represents a student's booking for an IELTS exam.
    
    This model manages:
    - Payment status and booking state
    - Module completion tracking for all IELTS modules
    - Sequential module unlocking system
    - Timestamps for module start and completion
    
    Key Features:
    - Sequential module progression (Writing → Reading → Listening → Speaking)
    - Payment status tracking
    - Module availability logic
    - Completion timestamp tracking
    """
    
    # =============================================================================
    # BOOKING STATUS CHOICES
    # =============================================================================
    # Define possible states for the booking throughout its lifecycle
    STATUS_CHOICES = [
        ('pending', 'Pending'),           # Initial state after booking creation
        ('paid', 'Paid'),                 # Payment successful, exam available
        ('failed', 'Failed'),             # Payment failed
        ('in_progress', 'In Progress'),   # Student has started taking modules
        ('completed', 'Completed'),       # All modules completed
        ('expired', 'Expired'),           # Booking expired
        ('cancelled', 'Cancelled'),       # Booking cancelled
        ('refund_requested', 'Refund Requested'),  # Refund requested
        ('refunded', 'Refunded'),         # Refund processed
    ]
    
    # =============================================================================
    # RELATIONSHIPS
    # =============================================================================
    # Link to the student who made the booking
    student_id = models.IntegerField(help_text="ID of the student who made the booking")
    
    # Link to the specific exam that was booked
    exam = models.ForeignKey('CreateExam', on_delete=models.CASCADE, related_name="bookings")
    
    # =============================================================================
    # PAYMENT AND STATUS FIELDS
    # =============================================================================
    paid = models.BooleanField(default=False)  # Whether payment has been completed
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Current booking status
    
    # =============================================================================
    # MODULE COMPLETION TRACKING
    # =============================================================================
    # Track completion status for each IELTS module
    # These fields control the sequential module unlocking system
    writing_completed = models.BooleanField(default=False)   # Writing module completion
    reading_completed = models.BooleanField(default=False)   # Reading module completion
    listening_completed = models.BooleanField(default=False) # Listening module completion
    speaking_completed = models.BooleanField(default=False)  # Speaking module completion
    
    # =============================================================================
    # MODULE START TIMESTAMPS
    # =============================================================================
    # Track when each module was started for analytics and debugging
    writing_started_at = models.DateTimeField(null=True, blank=True)   # When writing was started
    reading_started_at = models.DateTimeField(null=True, blank=True)   # When reading was started
    listening_started_at = models.DateTimeField(null=True, blank=True) # When listening was started
    speaking_started_at = models.DateTimeField(null=True, blank=True)  # When speaking was started
    
    # =============================================================================
    # MODULE COMPLETION TIMESTAMPS
    # =============================================================================
    # Track when each module was completed for analytics and reporting
    writing_completed_at = models.DateTimeField(null=True, blank=True)   # When writing was completed
    reading_completed_at = models.DateTimeField(null=True, blank=True)   # When reading was completed
    listening_completed_at = models.DateTimeField(null=True, blank=True) # When listening was completed
    speaking_completed_at = models.DateTimeField(null=True, blank=True)  # When speaking was completed
    
    # =============================================================================
    # AUDIT FIELDS
    # =============================================================================
    # Track when the booking was created and last updated
    created_at = models.DateTimeField(auto_now_add=True)  # When booking was created
    updated_at = models.DateTimeField(auto_now=True)      # When booking was last updated

    class Meta:
        """
        Meta configuration for the ExamBooking model.
        
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        - ordering: Order by creation date (newest first)
        - indexes: Performance optimization for common queries
        """
        db_table = 'exam_bookings'
        verbose_name = 'Exam Booking'
        verbose_name_plural = 'Exam Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['exam']),
            models.Index(fields=['status']),
            models.Index(fields=['paid']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """
        String representation of the booking for admin interface and debugging.
        
        Returns:
            str: Human-readable description of the booking
        """
        return f"Student {self.student_id} booked {self.exam} ({self.status})"
    
    def get_next_available_module(self):
        """
        Get the next available module based on completion status.
        
        This method implements the sequential module unlocking logic:
        - Writing is available first (after payment)
        - Reading becomes available after writing completion
        - Listening becomes available after reading completion
        - Speaking becomes available after listening completion
        
        Returns:
            str: Name of the next module to unlock, or 'completed' if all done
        """
        if not self.writing_completed:
            return 'writing'  # Writing is the first module
        elif not self.reading_completed:
            return 'reading'  # Reading unlocks after writing
        elif not self.listening_completed:
            return 'listening'  # Listening unlocks after reading
        elif not self.speaking_completed:
            return 'speaking'  # Speaking unlocks after listening
        else:
            return 'completed'  # All modules completed
    
    def is_module_available(self, module_name):
        """
        Check if a specific module is available for the student.
        
        This method determines module availability based on:
        - Sequential completion requirements
        - Current implementation status of modules
        
        Args:
            module_name (str): Name of the module to check ('writing', 'reading', etc.)
            
        Returns:
            bool: True if module is available, False otherwise
        """
        if module_name == 'writing':
            return self.paid and not self.writing_completed  # Writing available after payment
        elif module_name == 'reading':
            return self.writing_completed and not self.reading_completed  # Reading unlocks after writing completion
        elif module_name == 'listening':
            return self.reading_completed and not self.listening_completed  # Listening unlocks after reading
        elif module_name == 'speaking':
            return self.listening_completed and not self.speaking_completed  # Speaking unlocks after listening
        return False
    
    def mark_module_started(self, module_name):
        """
        Mark a module as started and record the timestamp.
        
        Args:
            module_name (str): Name of the module being started
        """
        if module_name == 'writing':
            self.writing_started_at = timezone.now()
        elif module_name == 'reading':
            self.reading_started_at = timezone.now()
        elif module_name == 'listening':
            self.listening_started_at = timezone.now()
        elif module_name == 'speaking':
            self.speaking_started_at = timezone.now()
        
        self.save()
    
    def mark_module_completed(self, module_name):
        """
        Mark a module as completed and record the timestamp.
        
        Args:
            module_name (str): Name of the module being completed
        """
        if module_name == 'writing':
            self.writing_completed = True
            self.writing_completed_at = timezone.now()
        elif module_name == 'reading':
            self.reading_completed = True
            self.reading_completed_at = timezone.now()
        elif module_name == 'listening':
            self.listening_completed = True
            self.listening_completed_at = timezone.now()
        elif module_name == 'speaking':
            self.speaking_completed = True
            self.speaking_completed_at = timezone.now()
        
        # Update overall status
        if self.writing_completed and self.reading_completed and self.listening_completed and self.speaking_completed:
            self.status = 'completed'
        
        self.save()
    
    def get_progress_percentage(self):
        """
        Calculate the overall progress percentage across all modules.
        
        Returns:
            int: Percentage of modules completed (0-100)
        """
        completed_modules = sum([
            self.writing_completed,
            self.reading_completed,
            self.listening_completed,
            self.speaking_completed
        ])
        
        return int((completed_modules / 4) * 100)
