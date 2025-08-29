# =============================================================================
# TEST REGISTRY MODEL
# =============================================================================
# This model serves as a central registry for all available reading tests.
# It provides intelligent test management, load balancing, and quality control.
# =============================================================================

from django.db import models
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Avg, Count
import logging

# Set up logging for debugging and monitoring
logger = logging.getLogger(__name__)

class TestRegistry(models.Model):
    """
    TestRegistry: Central registry for managing all available reading tests.
    
    This model acts as a "phone book" for all tests, ensuring:
    1. No orphaned test IDs (tests that don't exist)
    2. Intelligent test selection based on usage patterns
    3. Load balancing across available tests
    4. Quality control and monitoring
    5. Future scalability for advanced features
    
    Think of this as a "test manager" that knows about all tests
    and helps choose the best one for each student.
    """
    
    # =============================================================================
    # CORE FIELDS - Essential information about each test
    # =============================================================================
    
    # Primary identifier - this is the unique test ID that gets used in exam sessions
    # This field is the "bridge" between the registry and the actual ReadingTest
    test_id = models.UUIDField(
        primary_key=True,  # This makes test_id the main identifier
        help_text="Unique identifier for the test (links to ReadingTest.test_id)"
    )
    
    # Human-readable name for the test (e.g., "Cambridge IELTS 15 Test 1")
    # This helps administrators identify tests easily
    test_name = models.CharField(
        max_length=255,  # Maximum 255 characters for the name
        help_text="Human-readable name for the test (e.g., 'Cambridge IELTS 15 Test 1')"
    )
    
    # Which organization this test belongs to (for multi-tenant support)
    # This ensures tests are isolated between different organizations
    organization_id = models.IntegerField(
        help_text="Organization ID that owns this test (for multi-tenant isolation)"
    )
    
    # =============================================================================
    # STATUS FIELDS - Control whether tests are available for use
    # =============================================================================
    
    # Whether this test is currently available for students to take
    # False = test is disabled/maintenance mode
    # True = test is active and can be assigned to students
    is_active = models.BooleanField(
        default=True,  # New tests are active by default
        help_text="Whether this test is currently available for students (True=active, False=disabled)"
    )
    
    # Whether this test is featured/premium (for future premium features)
    # Featured tests might be shown first or available only to premium users
    is_featured = models.BooleanField(
        default=False,  # Most tests are not featured by default
        help_text="Whether this is a featured/premium test (for future premium features)"
    )
    
    # =============================================================================
    # USAGE TRACKING FIELDS - Monitor how tests are being used
    # =============================================================================
    
    # How many times this test has been assigned to students
    # This helps with load balancing (use less-used tests first)
    usage_count = models.IntegerField(
        default=0,  # Start at 0 when test is first registered
        help_text="Number of times this test has been assigned to students (for load balancing)"
    )
    
    # When this test was last assigned to a student
    # This helps with rotation (use older tests first)
    last_used = models.DateTimeField(
        auto_now=True,  # Automatically update whenever the record is saved
        help_text="When this test was last assigned to a student (for rotation)"
    )
    
    # =============================================================================
    # TIMESTAMP FIELDS - Track when tests were created and modified
    # =============================================================================
    
    # When this test was first registered in the system
    # This helps track test age and lifecycle
    created_at = models.DateTimeField(
        auto_now_add=True,  # Set automatically when record is first created
        help_text="When this test was first registered in the system"
    )
    
    # When this test was last modified (any field changed)
    # This helps track when test properties were last updated
    updated_at = models.DateTimeField(
        auto_now=True,  # Automatically update whenever any field changes
        help_text="When this test was last modified (any field changed)"
    )
    
    # =============================================================================
    # FUTURE-READY FIELDS - For upcoming features
    # =============================================================================
    
    # Test category (Academic, General Training, etc.)
    # This will be used for filtering tests by type
    test_category = models.CharField(
        max_length=50,  # Maximum 50 characters for category name
        default='Academic',  # Default to Academic IELTS
        help_text="Test category (Academic, General Training, etc.)"
    )
    
    # Difficulty level (Easy, Medium, Hard)
    # This will be used for adaptive difficulty selection
    difficulty_level = models.CharField(
        max_length=20,  # Maximum 20 characters for difficulty
        default='Medium',  # Default to Medium difficulty
        help_text="Difficulty level (Easy, Medium, Hard) for adaptive selection"
    )
    
    # Target band score (6.0, 7.0, 8.0, etc.)
    # This will be used for personalized test selection
    target_band_score = models.CharField(
        max_length=10,  # Maximum 10 characters (e.g., "7.5")
        default='7.0',  # Default to Band 7.0
        help_text="Target band score for this test (e.g., '7.0', '8.5')"
    )
    
    # Rotation priority (higher number = higher priority)
    # This will be used for custom test selection order
    rotation_priority = models.IntegerField(
        default=0,  # Default priority (0 = normal priority)
        help_text="Rotation priority (higher number = selected first, 0 = normal priority)"
    )
    
    # =============================================================================
    # META CONFIGURATION - Django model settings
    # =============================================================================
    
    class Meta:
        """
        Meta configuration for the TestRegistry model.
        
        This tells Django how to handle the model:
        - db_table: Custom table name in database
        - ordering: Default order when querying records
        - indexes: Database indexes for better performance
        """
        db_table = 'test_registry'  # Custom table name (instead of default 'reading_testregistry')
        ordering = ['-rotation_priority', 'usage_count', 'last_used']  # Default order: high priority first, then least used, then oldest
        indexes = [
            # Index on organization_id for fast filtering by organization
            models.Index(fields=['organization_id']),
            # Index on is_active for fast filtering of active tests
            models.Index(fields=['is_active']),
            # Index on usage_count for fast load balancing queries
            models.Index(fields=['usage_count']),
            # Composite index for common queries
            models.Index(fields=['organization_id', 'is_active']),
        ]
        verbose_name = 'Test Registry Entry'  # Human-readable name in admin
        verbose_name_plural = 'Test Registry Entries'  # Plural form in admin
    
    # =============================================================================
    # STRING REPRESENTATION - How the model appears in admin and logs
    # =============================================================================
    
    def __str__(self):
        """
        String representation of the TestRegistry entry.
        
        This is what you see in Django admin, logs, and when printing the object.
        Format: "Test Name (Test ID) - Organization ID"
        """
        return f"{self.test_name} ({self.test_id}) - Org {self.organization_id}"
    
    # =============================================================================
    # CORE METHODS - Main functionality for test management
    # =============================================================================
    
    def increment_usage(self):
        """
        Increment the usage count when this test is assigned to a student.
        
        This method is called whenever a test is successfully assigned.
        It updates both usage_count and last_used fields.
        
        Usage:
            test_registry.increment_usage()  # Call this when test is assigned
        """
        # Increment the usage counter
        self.usage_count += 1
        
        # Update the last used timestamp to now
        self.last_used = timezone.now()
        
        # Save the changes to database
        self.save(update_fields=['usage_count', 'last_used'])
        
        # Log the usage for monitoring
        logger.info(f"Test {self.test_id} usage incremented to {self.usage_count}")
    
    def deactivate(self, reason="Manual deactivation"):
        """
        Deactivate this test (mark as unavailable).
        
        This is used when a test needs to be taken offline for maintenance
        or when it's found to have issues.
        
        Args:
            reason (str): Why the test is being deactivated (for logging)
        
        Usage:
            test_registry.deactivate("Found duplicate questions")
        """
        # Mark the test as inactive
        self.is_active = False
        
        # Save the change
        self.save(update_fields=['is_active'])
        
        # Log the deactivation
        logger.warning(f"Test {self.test_id} deactivated: {reason}")
        
        # Clear any cached data for this test
        cache.delete(f"test_registry_{self.test_id}")
    
    def activate(self, reason="Manual activation"):
        """
        Activate this test (mark as available).
        
        This is used when a test is ready to be used again after maintenance
        or when issues have been resolved.
        
        Args:
            reason (str): Why the test is being activated (for logging)
        
        Usage:
            test_registry.activate("Issues resolved")
        """
        # Mark the test as active
        self.is_active = True
        
        # Save the change
        self.save(update_fields=['is_active'])
        
        # Log the activation
        logger.info(f"Test {self.test_id} activated: {reason}")
        
        # Clear any cached data for this test
        cache.delete(f"test_registry_{self.test_id}")
    
    def is_available(self):
        """
        Check if this test is currently available for assignment.
        
        This method checks multiple conditions to determine if a test
        can be assigned to a student.
        
        Returns:
            bool: True if test can be assigned, False otherwise
        
        Usage:
            if test_registry.is_available():
                # Assign test to student
        """
        # Test must be active
        if not self.is_active:
            return False
        
        # Test must exist in the ReadingTest table (safety check)
        try:
            from reading.models import ReadingTest
            ReadingTest.objects.get(test_id=self.test_id)
        except ReadingTest.DoesNotExist:
            # Test doesn't exist in ReadingTest table - mark as inactive
            self.deactivate("Test not found in ReadingTest table")
            return False
        
        # All checks passed - test is available
        return True
    
    # =============================================================================
    # STATIC METHODS - Class-level operations for test management
    # =============================================================================
    
    @classmethod
    def get_available_test(cls, organization_id, strategy='balanced'):
        """
        Get the best available test for an organization.
        
        This is the main method used by the exam start process to select
        which test to assign to a student.
        
        Args:
            organization_id (int): ID of the organization requesting a test
            strategy (str): Selection strategy ('balanced', 'round_robin', 'random')
        
        Returns:
            TestRegistry or None: The selected test, or None if no tests available
        
        Usage:
            test = TestRegistry.get_available_test(organization_id=1)
            if test:
                test.increment_usage()  # Mark as used
        """
        # Get all active tests for this organization
        available_tests = cls.objects.filter(
            organization_id=organization_id,
            is_active=True
        )
        
        # If no tests available, return None
        if not available_tests.exists():
            logger.warning(f"No available tests for organization {organization_id}")
            return None
        
        # Apply selection strategy
        if strategy == 'balanced':
            # Balanced strategy: prioritize tests with lower usage count
            # This distributes load evenly across all available tests
            selected_test = available_tests.order_by('usage_count', 'last_used').first()
        elif strategy == 'round_robin':
            # Round robin strategy: select the oldest used test
            # This ensures all tests get used in rotation
            selected_test = available_tests.order_by('last_used').first()
        elif strategy == 'random':
            # Random strategy: select any available test randomly
            # This provides variety but may not balance load
            import random
            test_list = list(available_tests)
            selected_test = random.choice(test_list) if test_list else None
        else:
            # Default to balanced strategy
            selected_test = available_tests.order_by('usage_count', 'last_used').first()
        
        # Log the selection for monitoring
        if selected_test:
            logger.info(f"Selected test {selected_test.test_id} for organization {organization_id} using {strategy} strategy")
        
        return selected_test
    
    @classmethod
    def register_test(cls, test_id, test_name, organization_id, **kwargs):
        """
        Register a new test in the registry.
        
        This method is called when a new ReadingTest is created to ensure
        it's properly registered in the TestRegistry.
        
        Args:
            test_id (UUID): The test ID from ReadingTest
            test_name (str): Human-readable test name
            organization_id (int): Organization that owns the test
            **kwargs: Additional fields (test_category, difficulty_level, etc.)
        
        Returns:
            TestRegistry: The created or updated registry entry
        
        Usage:
            TestRegistry.register_test(
                test_id=uuid.uuid4(),
                test_name="Cambridge IELTS 15 Test 1",
                organization_id=1,
                test_category="Academic",
                difficulty_level="Medium"
            )
        """
        # Try to get existing registry entry
        registry_entry, created = cls.objects.get_or_create(
            test_id=test_id,  # Use test_id as the unique identifier
            defaults={
                'test_name': test_name,
                'organization_id': organization_id,
                **kwargs  # Include any additional fields
            }
        )
        
        # If entry already existed, update the fields
        if not created:
            # Update fields that might have changed
            registry_entry.test_name = test_name
            registry_entry.organization_id = organization_id
            
            # Update any additional fields provided
            for key, value in kwargs.items():
                if hasattr(registry_entry, key):
                    setattr(registry_entry, key, value)
            
            # Save the updates
            registry_entry.save()
        
        # Log the registration
        action = "created" if created else "updated"
        logger.info(f"Test registry entry {action}: {test_id} - {test_name}")
        
        return registry_entry
    
    @classmethod
    def cleanup_inactive_tests(cls, days_threshold=90, usage_threshold=10):
        """
        Automatically cleanup old and unused tests.
        
        This method is designed to be run periodically (e.g., daily cron job)
        to maintain the registry and remove tests that are no longer needed.
        
        Args:
            days_threshold (int): Days since last use to consider for cleanup
            usage_threshold (int): Minimum usage count to avoid cleanup
        
        Usage:
            TestRegistry.cleanup_inactive_tests()  # Run this periodically
        """
        # Calculate the cutoff date
        cutoff_date = timezone.now() - timezone.timedelta(days=days_threshold)
        
        # Find tests that haven't been used recently and have low usage
        old_tests = cls.objects.filter(
            last_used__lt=cutoff_date,  # Not used recently
            usage_count__lt=usage_threshold,  # Low usage count
            is_active=True  # Currently active
        )
        
        # Deactivate these tests
        deactivated_count = old_tests.count()
        old_tests.update(is_active=False)
        
        # Log the cleanup
        if deactivated_count > 0:
            logger.info(f"Auto-cleanup: Deactivated {deactivated_count} old/unused tests")
        
        return deactivated_count
    
    @classmethod
    def get_registry_stats(cls, organization_id=None):
        """
        Get statistics about the test registry.
        
        This method provides insights into test usage patterns and helps
        with monitoring and decision-making.
        
        Args:
            organization_id (int, optional): Filter stats by organization
        
        Returns:
            dict: Statistics about the registry
        
        Usage:
            stats = TestRegistry.get_registry_stats(organization_id=1)
            print(f"Active tests: {stats['active_count']}")
        """
        # Base queryset
        queryset = cls.objects
        
        # Filter by organization if specified
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        # Calculate statistics
        stats = {
            'total_tests': queryset.count(),
            'active_tests': queryset.filter(is_active=True).count(),
            'inactive_tests': queryset.filter(is_active=False).count(),
            'featured_tests': queryset.filter(is_featured=True).count(),
            'avg_usage': queryset.aggregate(Avg('usage_count'))['usage_count__avg'] or 0,
            'total_usage': queryset.aggregate(Count('usage_count'))['usage_count__count'] or 0,
        }
        
        return stats
    
    # =============================================================================
    # CACHE METHODS - Performance optimization
    # =============================================================================
    
    def get_cache_key(self):
        """
        Get the cache key for this test registry entry.
        
        This is used for caching test data to improve performance.
        
        Returns:
            str: Cache key for this test
        
        Usage:
            cache_key = test_registry.get_cache_key()
            cached_data = cache.get(cache_key)
        """
        return f"test_registry_{self.test_id}"
    
    def clear_cache(self):
        """
        Clear cached data for this test registry entry.
        
        This is called when test data is updated to ensure
        cached data doesn't become stale.
        
        Usage:
            test_registry.clear_cache()  # Clear any cached data
        """
        cache.delete(self.get_cache_key())
    
    # =============================================================================
    # VALIDATION METHODS - Data integrity checks
    # =============================================================================
    
    def clean(self):
        """
        Validate the model data before saving.
        
        This method is called by Django before saving to ensure
        data integrity and business rules are followed.
        
        Usage:
            test_registry.full_clean()  # This calls clean() method
        """
        from django.core.exceptions import ValidationError
        
        # Validate that test_id is not empty
        if not self.test_id:
            raise ValidationError("Test ID is required")
        
        # Validate that test_name is not empty
        if not self.test_name or not self.test_name.strip():
            raise ValidationError("Test name is required")
        
        # Validate that organization_id is positive
        if self.organization_id <= 0:
            raise ValidationError("Organization ID must be positive")
        
        # Validate difficulty level
        valid_difficulties = ['Easy', 'Medium', 'Hard']
        if self.difficulty_level not in valid_difficulties:
            raise ValidationError(f"Difficulty level must be one of: {valid_difficulties}")
        
        # Validate usage count is not negative
        if self.usage_count < 0:
            raise ValidationError("Usage count cannot be negative")
    
    def save(self, *args, **kwargs):
        """
        Override save method to add custom logic.
        
        This method is called whenever a TestRegistry entry is saved.
        It adds custom validation and logging.
        
        Args:
            *args: Standard Django save arguments
            **kwargs: Standard Django save keyword arguments
        
        Usage:
            test_registry.save()  # This calls the overridden save method
        """
        # Validate the data before saving
        self.full_clean()
        
        # Call the parent save method
        super().save(*args, **kwargs)
        
        # Clear cache after saving
        self.clear_cache()
        
        # Log the save operation
        logger.debug(f"Test registry entry saved: {self.test_id}")
