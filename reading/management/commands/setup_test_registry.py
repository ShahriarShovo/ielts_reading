# =============================================================================
# DJANGO MANAGEMENT COMMAND: Setup Test Registry
# =============================================================================
# This command sets up the TestRegistry system by:
# 1. Creating the test_registry table (via migration)
# 2. Registering all existing ReadingTest objects
# 3. Validating consistency between tables
# 4. Generating a health report
# =============================================================================

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from reading.services.test_registry_service import TestRegistryService
from reading.models.test_registry import TestRegistry
from reading.models import ReadingTest
import logging

# Set up logging for the command
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Django management command to set up the TestRegistry system.
    
    This command is used to initialize the TestRegistry with all existing
    ReadingTest objects and validate the system's health.
    
    Usage:
        python manage.py setup_test_registry
        
    Options:
        --force: Force re-registration of all tests (even if already registered)
        --validate-only: Only validate consistency, don't register new tests
        --health-report: Generate and display health report
    """
    
    # Command help text (shown when running --help)
    help = 'Set up the TestRegistry system with existing ReadingTest objects'
    
    def add_arguments(self, parser):
        """
        Add command-line arguments to the parser.
        
        This method defines the options that can be passed to the command.
        
        Args:
            parser: Django's argument parser object
        """
        # Add --force flag to force re-registration
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-registration of all tests (even if already registered)'
        )
        
        # Add --validate-only flag to only validate consistency
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate consistency, don\'t register new tests'
        )
        
        # Add --health-report flag to generate health report
        parser.add_argument(
            '--health-report',
            action='store_true',
            help='Generate and display health report'
        )
        
        # Add --verbose flag for detailed output
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed output during setup'
        )
    
    def handle(self, *args, **options):
        """
        Main command handler - executes the setup process.
        
        This method is called when the command is run. It orchestrates
        the entire setup process including registration, validation, and reporting.
        
        Args:
            *args: Additional positional arguments
            **options: Command-line options (force, validate-only, etc.)
        """
        # Extract options for easier access
        force = options['force']
        validate_only = options['validate_only']
        health_report = options['health_report']
        verbose = options['verbose']
        
        # Display command header
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        self.stdout.write(
            self.style.SUCCESS('TEST REGISTRY SETUP COMMAND')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        
        # Log command execution
        logger.info("Test Registry setup command started")
        logger.info(f"Options: force={force}, validate_only={validate_only}, health_report={health_report}")
        
        try:
            # =============================================================================
            # STEP 1: VALIDATE DATABASE CONNECTION
            # =============================================================================
            # Ensure we can connect to the database and access required tables
            # =============================================================================
            
            self.stdout.write("Step 1: Validating database connection...")
            
            # Test database connection by counting ReadingTest objects
            try:
                reading_test_count = ReadingTest.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Database connection successful")
                )
                self.stdout.write(
                    f"  Found {reading_test_count} ReadingTest objects"
                )
            except Exception as e:
                # Database connection failed
                self.stdout.write(
                    self.style.ERROR(f"✗ Database connection failed: {str(e)}")
                )
                raise CommandError(f"Database connection failed: {str(e)}")
            
            # =============================================================================
            # STEP 2: CHECK TEST REGISTRY TABLE
            # =============================================================================
            # Ensure the test_registry table exists and is accessible
            # =============================================================================
            
            self.stdout.write("Step 2: Checking TestRegistry table...")
            
            try:
                # Test TestRegistry table access
                registry_count = TestRegistry.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f"✓ TestRegistry table accessible")
                )
                self.stdout.write(
                    f"  Found {registry_count} existing registry entries"
                )
            except Exception as e:
                # TestRegistry table doesn't exist or is not accessible
                self.stdout.write(
                    self.style.ERROR(f"✗ TestRegistry table not accessible: {str(e)}")
                )
                self.stdout.write(
                    self.style.WARNING("Please run migrations first: python manage.py migrate")
                )
                raise CommandError(f"TestRegistry table not accessible: {str(e)}")
            
            # =============================================================================
            # STEP 3: VALIDATE CONSISTENCY (ALWAYS RUN)
            # =============================================================================
            # Check for orphaned entries and unregistered tests
            # =============================================================================
            
            self.stdout.write("Step 3: Validating registry consistency...")
            
            # Validate consistency between ReadingTest and TestRegistry tables
            consistency = TestRegistryService.validate_registry_consistency()
            
            # Display consistency results
            self.stdout.write(
                f"  Orphaned registry entries: {len(consistency['orphaned_registry_entries'])}"
            )
            self.stdout.write(
                f"  Unregistered tests: {len(consistency['unregistered_tests'])}"
            )
            self.stdout.write(
                f"  Total registry entries: {consistency['total_registry_entries']}"
            )
            self.stdout.write(
                f"  Total reading tests: {consistency['total_reading_tests']}"
            )
            
            if consistency['orphaned_registry_entries']:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  Found {len(consistency['orphaned_registry_entries'])} orphaned entries")
                )
            
            if consistency['unregistered_tests']:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  Found {len(consistency['unregistered_tests'])} unregistered tests")
                )
            
            # =============================================================================
            # STEP 4: REGISTER TESTS (UNLESS VALIDATE-ONLY)
            # =============================================================================
            # Register all ReadingTest objects in TestRegistry
            # =============================================================================
            
            if not validate_only:
                self.stdout.write("Step 4: Registering tests in TestRegistry...")
                
                # Check if we should force re-registration
                if force:
                    self.stdout.write("  Force mode: Re-registering all tests...")
                    
                    # Delete all existing registry entries
                    deleted_count = TestRegistry.objects.all().delete()[0]
                    self.stdout.write(f"  Deleted {deleted_count} existing registry entries")
                
                # Register all existing tests
                registered_count = TestRegistryService.auto_register_existing_tests()
                
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Registration complete")
                )
                self.stdout.write(
                    f"  Registered {registered_count} tests"
                )
                
                # Validate consistency again after registration
                self.stdout.write("  Re-validating consistency...")
                post_consistency = TestRegistryService.validate_registry_consistency()
                
                self.stdout.write(
                    f"  Orphaned entries after registration: {len(post_consistency['orphaned_registry_entries'])}"
                )
                self.stdout.write(
                    f"  Unregistered tests after registration: {len(post_consistency['unregistered_tests'])}"
                )
            else:
                self.stdout.write("Step 4: Skipped (validate-only mode)")
            
            # =============================================================================
            # STEP 5: GENERATE HEALTH REPORT
            # =============================================================================
            # Generate comprehensive health report
            # =============================================================================
            
            self.stdout.write("Step 5: Generating health report...")
            
            # Get comprehensive health report
            health = TestRegistryService.get_registry_health_report()
            
            # Display health report
            self.stdout.write(
                self.style.SUCCESS(f"✓ Health report generated")
            )
            self.stdout.write(
                f"  Status: {health['status']}"
            )
            self.stdout.write(
                f"  Health Score: {health['health_score']}/100"
            )
            self.stdout.write(
                f"  Active Tests: {health['statistics']['active_tests']}"
            )
            self.stdout.write(
                f"  Total Tests: {health['statistics']['total_tests']}"
            )
            self.stdout.write(
                f"  Featured Tests: {health['statistics']['featured_tests']}"
            )
            self.stdout.write(
                f"  Average Usage: {health['statistics']['avg_usage']:.1f}"
            )
            
            # Display recommendations if any
            if health['recommendations']:
                self.stdout.write("  Recommendations:")
                for recommendation in health['recommendations']:
                    self.stdout.write(f"    • {recommendation}")
            
            # =============================================================================
            # STEP 6: DISPLAY DETAILED STATISTICS (IF VERBOSE)
            # =============================================================================
            # Show detailed statistics for debugging
            # =============================================================================
            
            if verbose:
                self.stdout.write("Step 6: Detailed statistics...")
                
                # Get all registry entries with details
                registry_entries = TestRegistry.objects.all().order_by('usage_count', 'last_used')
                
                self.stdout.write("  Registry entries:")
                for entry in registry_entries:
                    self.stdout.write(
                        f"    • {entry.test_name} (ID: {entry.test_id})"
                    )
                    self.stdout.write(
                        f"      - Active: {entry.is_active}, Usage: {entry.usage_count}, Last Used: {entry.last_used}"
                    )
                
                # Get all reading tests
                reading_tests = ReadingTest.objects.all()
                self.stdout.write("  Reading tests:")
                for test in reading_tests:
                    self.stdout.write(
                        f"    • {test.test_name} (ID: {test.test_id})"
                    )
            
            # =============================================================================
            # STEP 7: FINAL VALIDATION
            # =============================================================================
            # Final check to ensure everything is working
            # =============================================================================
            
            self.stdout.write("Step 7: Final validation...")
            
            # Test the test selection functionality
            try:
                # Try to get a test for organization 1 (or any existing organization)
                test = TestRegistryService.get_best_test_for_organization(organization_id=1)
                
                if test:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Test selection working")
                    )
                    self.stdout.write(
                        f"  Selected test: {test.test_name} (ID: {test.test_id})"
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  No tests available for organization 1")
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Test selection failed: {str(e)}")
                )
            
            # =============================================================================
            # COMMAND COMPLETION
            # =============================================================================
            # Display completion message and summary
            # =============================================================================
            
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.SUCCESS("TEST REGISTRY SETUP COMPLETE")
            )
            self.stdout.write("=" * 60)
            
            # Display summary
            final_stats = TestRegistry.objects.count()
            self.stdout.write(f"Total registry entries: {final_stats}")
            self.stdout.write(f"Health status: {health['status']} ({health['health_score']}/100)")
            
            if health['health_score'] >= 90:
                self.stdout.write(
                    self.style.SUCCESS("✓ System is healthy and ready for use")
                )
            elif health['health_score'] >= 70:
                self.stdout.write(
                    self.style.WARNING("⚠️  System is functional but has some issues")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("✗ System has significant issues that need attention")
                )
            
            # Log command completion
            logger.info("Test Registry setup command completed successfully")
            
        except Exception as e:
            # Handle any errors during setup
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.ERROR("TEST REGISTRY SETUP FAILED")
            )
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )
            
            # Log the error
            logger.error(f"Test Registry setup command failed: {str(e)}")
            
            # Re-raise as CommandError
            raise CommandError(f"Setup failed: {str(e)}")
