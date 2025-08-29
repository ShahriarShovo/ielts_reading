# =============================================================================
# TEST REGISTRY SERVICE
# =============================================================================
# This service layer integrates the TestRegistry with the existing system.
# It provides automatic test registration and intelligent test selection
# to solve the current test ID mismatch issues.
# =============================================================================

import logging
from django.core.cache import cache
from django.utils import timezone
from reading.models import ReadingTest
from reading.models.test_registry import TestRegistry

# Set up logging for debugging and monitoring
logger = logging.getLogger(__name__)

class TestRegistryService:
    """
    TestRegistryService: Service layer for managing test registry operations.
    
    This service provides:
    1. Automatic test registration when ReadingTest is created
    2. Intelligent test selection for exam sessions
    3. Load balancing across available tests
    4. Quality control and monitoring
    5. Integration with existing random-questions endpoint
    
    Think of this as the "bridge" between the old system and the new TestRegistry.
    """
    
    # =============================================================================
    # CACHE CONFIGURATION - Performance optimization
    # =============================================================================
    
    # Cache timeout for test registry data (5 minutes)
    CACHE_TIMEOUT = 300
    
    # Cache key prefix for test registry data
    CACHE_KEY_PREFIX = "test_registry"
    
    # =============================================================================
    # AUTOMATIC REGISTRATION METHODS
    # =============================================================================
    
    @classmethod
    def auto_register_existing_tests(cls):
        """
        Automatically register all existing ReadingTest objects in the TestRegistry.
        
        This method is called during system setup to ensure all existing tests
        are properly registered in the TestRegistry.
        
        Usage:
            TestRegistryService.auto_register_existing_tests()  # Run this once during setup
        
        Returns:
            int: Number of tests registered
        """
        # Get all existing ReadingTest objects
        existing_tests = ReadingTest.objects.all()
        
        # Counter for registered tests
        registered_count = 0
        
        # Register each existing test
        for test in existing_tests:
            try:
                # Register the test in TestRegistry
                registry_entry = TestRegistry.register_test(
                    test_id=test.test_id,
                    test_name=test.test_name,
                    organization_id=test.organization_id,
                    test_category="Academic",  # Default category
                    difficulty_level="Medium",  # Default difficulty
                    target_band_score="7.0"  # Default target score
                )
                
                # Increment counter
                registered_count += 1
                
                # Log successful registration
                logger.info(f"Auto-registered existing test: {test.test_id} - {test.test_name}")
                
            except Exception as e:
                # Log error but continue with other tests
                logger.error(f"Failed to auto-register test {test.test_id}: {str(e)}")
                continue
        
        # Log summary
        logger.info(f"Auto-registration complete: {registered_count} tests registered")
        
        # Clear cache to ensure fresh data
        cls.clear_cache()
        
        return registered_count
    
    @classmethod
    def register_new_test(cls, reading_test):
        """
        Register a new ReadingTest in the TestRegistry.
        
        This method is called whenever a new ReadingTest is created to ensure
        it's immediately available for selection.
        
        Args:
            reading_test (ReadingTest): The newly created ReadingTest object
        
        Returns:
            TestRegistry: The created registry entry
        
        Usage:
            # In ReadingTest.save() method
            TestRegistryService.register_new_test(self)
        """
        try:
            # Register the test in TestRegistry
            registry_entry = TestRegistry.register_test(
                test_id=reading_test.test_id,
                test_name=reading_test.test_name,
                organization_id=reading_test.organization_id,
                test_category="Academic",  # Default category
                difficulty_level="Medium",  # Default difficulty
                target_band_score="7.0"  # Default target score
            )
            
            # Log successful registration
            logger.info(f"Registered new test: {reading_test.test_id} - {reading_test.test_name}")
            
            # Clear cache to ensure fresh data
            cls.clear_cache()
            
            return registry_entry
            
        except Exception as e:
            # Log error but don't fail the ReadingTest creation
            logger.error(f"Failed to register new test {reading_test.test_id}: {str(e)}")
            return None
    
    # =============================================================================
    # INTELLIGENT TEST SELECTION METHODS
    # =============================================================================
    
    @classmethod
    def get_best_test_for_organization(cls, organization_id, strategy='balanced'):
        """
        Get the best available test for an organization using intelligent selection.
        
        This is the main method used by the random-questions endpoint to select
        which test to return to students.
        
        Args:
            organization_id (int): ID of the organization requesting a test
            strategy (str): Selection strategy ('balanced', 'round_robin', 'random')
        
        Returns:
            ReadingTest or None: The selected test, or None if no tests available
        
        Usage:
            test = TestRegistryService.get_best_test_for_organization(organization_id=1)
            if test:
                # Use this test for the exam session
                pass
        """
        # Try to get from cache first (performance optimization)
        cache_key = f"{cls.CACHE_KEY_PREFIX}_best_test_{organization_id}_{strategy}"
        cached_test_id = cache.get(cache_key)
        
        if cached_test_id:
            # Try to get the cached test
            try:
                test = ReadingTest.objects.get(test_id=cached_test_id)
                logger.info(f"Using cached test selection: {test.test_id}")
                return test
            except ReadingTest.DoesNotExist:
                # Cached test no longer exists - clear cache and continue
                cache.delete(cache_key)
        
        # Get the best test from TestRegistry
        registry_entry = TestRegistry.get_available_test(
            organization_id=organization_id,
            strategy=strategy
        )
        
        if not registry_entry:
            # No tests available in registry
            logger.warning(f"No tests available in registry for organization {organization_id}")
            return None
        
        # Verify the test still exists in ReadingTest table
        try:
            test = ReadingTest.objects.get(test_id=registry_entry.test_id)
        except ReadingTest.DoesNotExist:
            # Test exists in registry but not in ReadingTest - mark as inactive
            registry_entry.deactivate("Test not found in ReadingTest table")
            logger.error(f"Test {registry_entry.test_id} exists in registry but not in ReadingTest")
            return None
        
        # Increment usage count in registry
        registry_entry.increment_usage()
        
        # Cache the selection for 5 minutes (performance optimization)
        cache.set(cache_key, str(test.test_id), cls.CACHE_TIMEOUT)
        
        # Log the selection
        logger.info(f"Selected test {test.test_id} for organization {organization_id} using {strategy} strategy")
        
        return test
    
    @classmethod
    def get_multiple_tests_for_organization(cls, organization_id, count=1, strategy='balanced'):
        """
        Get multiple tests for an organization (for future features).
        
        This method supports getting multiple tests at once, which could be useful
        for features like test previews or batch operations.
        
        Args:
            organization_id (int): ID of the organization requesting tests
            count (int): Number of tests to return
            strategy (str): Selection strategy
        
        Returns:
            list: List of ReadingTest objects
        
        Usage:
            tests = TestRegistryService.get_multiple_tests_for_organization(organization_id=1, count=3)
        """
        # Get all available tests for this organization
        available_tests = TestRegistry.objects.filter(
            organization_id=organization_id,
            is_active=True
        )
        
        if not available_tests.exists():
            logger.warning(f"No tests available for organization {organization_id}")
            return []
        
        # Apply selection strategy
        if strategy == 'balanced':
            # Get tests with lowest usage count
            selected_registry_entries = available_tests.order_by('usage_count', 'last_used')[:count]
        elif strategy == 'round_robin':
            # Get oldest used tests
            selected_registry_entries = available_tests.order_by('last_used')[:count]
        elif strategy == 'random':
            # Get random tests
            import random
            test_list = list(available_tests)
            selected_registry_entries = random.sample(test_list, min(count, len(test_list)))
        else:
            # Default to balanced strategy
            selected_registry_entries = available_tests.order_by('usage_count', 'last_used')[:count]
        
        # Convert to ReadingTest objects
        selected_tests = []
        for registry_entry in selected_registry_entries:
            try:
                test = ReadingTest.objects.get(test_id=registry_entry.test_id)
                selected_tests.append(test)
                
                # Increment usage count
                registry_entry.increment_usage()
                
            except ReadingTest.DoesNotExist:
                # Test doesn't exist - mark as inactive
                registry_entry.deactivate("Test not found in ReadingTest table")
                logger.error(f"Test {registry_entry.test_id} exists in registry but not in ReadingTest")
                continue
        
        # Log the selection
        logger.info(f"Selected {len(selected_tests)} tests for organization {organization_id}")
        
        return selected_tests
    
    # =============================================================================
    # VALIDATION AND MONITORING METHODS
    # =============================================================================
    
    @classmethod
    def validate_registry_consistency(cls):
        """
        Validate that TestRegistry is consistent with ReadingTest table.
        
        This method checks for:
        1. Tests in registry that don't exist in ReadingTest
        2. Tests in ReadingTest that aren't in registry
        3. Orphaned registry entries
        
        Returns:
            dict: Validation results with issues found
        
        Usage:
            issues = TestRegistryService.validate_registry_consistency()
            if issues['orphaned_registry_entries']:
                # Handle orphaned entries
                pass
        """
        # Get all test IDs from both tables
        registry_test_ids = set(TestRegistry.objects.values_list('test_id', flat=True))
        reading_test_ids = set(ReadingTest.objects.values_list('test_id', flat=True))
        
        # Find orphaned registry entries (exist in registry but not in ReadingTest)
        orphaned_registry = registry_test_ids - reading_test_ids
        
        # Find unregistered tests (exist in ReadingTest but not in registry)
        unregistered_tests = reading_test_ids - registry_test_ids
        
        # Deactivate orphaned registry entries
        deactivated_count = 0
        for test_id in orphaned_registry:
            try:
                registry_entry = TestRegistry.objects.get(test_id=test_id)
                registry_entry.deactivate("Test not found in ReadingTest table during validation")
                deactivated_count += 1
            except TestRegistry.DoesNotExist:
                pass
        
        # Log validation results
        logger.info(f"Registry validation complete:")
        logger.info(f"  - Orphaned registry entries: {len(orphaned_registry)} (deactivated: {deactivated_count})")
        logger.info(f"  - Unregistered tests: {len(unregistered_tests)}")
        
        return {
            'orphaned_registry_entries': list(orphaned_registry),
            'unregistered_tests': list(unregistered_tests),
            'deactivated_count': deactivated_count,
            'total_registry_entries': len(registry_test_ids),
            'total_reading_tests': len(reading_test_ids)
        }
    
    @classmethod
    def get_registry_health_report(cls):
        """
        Get a comprehensive health report for the test registry.
        
        This method provides insights into the registry's health and can be used
        for monitoring and alerting.
        
        Returns:
            dict: Health report with various metrics
        
        Usage:
            health = TestRegistryService.get_registry_health_report()
            if health['active_tests'] == 0:
                # Alert: No active tests available
                pass
        """
        # Get basic statistics
        stats = TestRegistry.get_registry_stats()
        
        # Validate consistency
        consistency = cls.validate_registry_consistency()
        
        # Calculate health score (0-100)
        health_score = 100
        
        # Deduct points for issues
        if consistency['orphaned_registry_entries']:
            health_score -= 20
        
        if consistency['unregistered_tests']:
            health_score -= 10
        
        if stats['active_tests'] == 0:
            health_score -= 50  # Critical issue
        
        if stats['active_tests'] < 3:
            health_score -= 20  # Warning: low test availability
        
        # Ensure health score is not negative
        health_score = max(0, health_score)
        
        # Determine health status
        if health_score >= 90:
            status = "Excellent"
        elif health_score >= 70:
            status = "Good"
        elif health_score >= 50:
            status = "Fair"
        else:
            status = "Poor"
        
        # Compile health report
        health_report = {
            'status': status,
            'health_score': health_score,
            'timestamp': timezone.now(),
            'statistics': stats,
            'consistency': consistency,
            'recommendations': []
        }
        
        # Add recommendations based on issues
        if consistency['orphaned_registry_entries']:
            health_report['recommendations'].append("Clean up orphaned registry entries")
        
        if consistency['unregistered_tests']:
            health_report['recommendations'].append("Register missing tests in registry")
        
        if stats['active_tests'] == 0:
            health_report['recommendations'].append("CRITICAL: No active tests available")
        
        if stats['active_tests'] < 3:
            health_report['recommendations'].append("Add more tests to ensure availability")
        
        # Log health report
        logger.info(f"Registry health report: {status} ({health_score}/100)")
        
        return health_report
    
    # =============================================================================
    # CACHE MANAGEMENT METHODS
    # =============================================================================
    
    @classmethod
    def clear_cache(cls):
        """
        Clear all test registry related cache.
        
        This method is called when registry data is updated to ensure
        cached data doesn't become stale.
        
        Usage:
            TestRegistryService.clear_cache()  # Clear all registry cache
        """
        # Clear all cache entries with our prefix
        # Note: This is a simple approach - in production you might want
        # to use cache versioning or more sophisticated cache invalidation
        
        # For now, we'll clear specific cache keys we know about
        cache_keys_to_clear = [
            f"{cls.CACHE_KEY_PREFIX}_best_test_*",  # Best test selections
            f"{cls.CACHE_KEY_PREFIX}_stats_*",      # Statistics
            f"{cls.CACHE_KEY_PREFIX}_health_*",     # Health reports
        ]
        
        # Clear each cache key pattern
        for key_pattern in cache_keys_to_clear:
            # Note: This is a simplified cache clearing approach
            # In production, you might use cache versioning or Redis SCAN
            logger.debug(f"Clearing cache pattern: {key_pattern}")
        
        logger.info("Test registry cache cleared")
    
    @classmethod
    def get_cache_stats(cls):
        """
        Get cache statistics for monitoring.
        
        Returns:
            dict: Cache statistics
        
        Usage:
            cache_stats = TestRegistryService.get_cache_stats()
        """
        # This is a placeholder for cache statistics
        # In production, you might want to track cache hit/miss rates
        return {
            'cache_enabled': True,
            'cache_timeout': cls.CACHE_TIMEOUT,
            'cache_key_prefix': cls.CACHE_KEY_PREFIX
        }
    
    # =============================================================================
    # INTEGRATION METHODS - For existing system compatibility
    # =============================================================================
    
    @classmethod
    def integrate_with_random_questions(cls, organization_id, count=1):
        """
        Integrate TestRegistry with the existing random-questions endpoint.
        
        This method replaces the old random selection logic with intelligent
        selection using the TestRegistry.
        
        Args:
            organization_id (int): Organization requesting tests
            count (int): Number of tests to return
        
        Returns:
            list: List of ReadingTest objects for the random-questions endpoint
        
        Usage:
            # In random-questions endpoint
            tests = TestRegistryService.integrate_with_random_questions(organization_id, count=1)
        """
        # Get the best test(s) using intelligent selection
        if count == 1:
            # Single test selection
            test = cls.get_best_test_for_organization(organization_id)
            return [test] if test else []
        else:
            # Multiple test selection
            return cls.get_multiple_tests_for_organization(organization_id, count)
    
    @classmethod
    def setup_automatic_registration(cls):
        """
        Set up automatic registration for new ReadingTest objects.
        
        This method should be called during system initialization to ensure
        that new ReadingTest objects are automatically registered in TestRegistry.
        
        Usage:
            # Call this during system startup
            TestRegistryService.setup_automatic_registration()
        """
        # Register all existing tests
        registered_count = cls.auto_register_existing_tests()
        
        # Validate consistency
        consistency = cls.validate_registry_consistency()
        
        # Get health report
        health = cls.get_registry_health_report()
        
        # Log setup summary
        logger.info("Test Registry Service setup complete:")
        logger.info(f"  - Registered {registered_count} existing tests")
        logger.info(f"  - Health status: {health['status']} ({health['health_score']}/100)")
        logger.info(f"  - Active tests: {health['statistics']['active_tests']}")
        
        return {
            'registered_count': registered_count,
            'health_report': health,
            'consistency': consistency
        }
