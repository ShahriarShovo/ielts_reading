# =============================================================================
# MIGRATION: Create Test Registry Table
# =============================================================================
# This migration creates the test_registry table which serves as a central
# registry for managing all available reading tests.
# =============================================================================

from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    """
    Migration to create the TestRegistry table.
    
    This migration:
    1. Creates the test_registry table with all necessary fields
    2. Sets up database indexes for optimal performance
    3. Establishes the foundation for intelligent test management
    
    The TestRegistry will solve the current test ID mismatch issues
    and provide a robust foundation for future test management features.
    """
    
    # Dependencies: This migration depends on the previous migration
    # that created the basic reading models (ReadingTest, Passage, etc.)
    dependencies = [
        ('reading', '0001_initial'),  # Replace with your actual previous migration
    ]
    
    # Operations to perform during this migration
    operations = [
        # =============================================================================
        # CREATE TEST REGISTRY TABLE
        # =============================================================================
        # This creates the main test_registry table with all the fields
        # needed for intelligent test management and load balancing.
        # =============================================================================
        migrations.CreateModel(
            # Name of the model in Django
            name='TestRegistry',
            
            # List of fields to create in the table
            fields=[
                # =============================================================================
                # PRIMARY KEY FIELD
                # =============================================================================
                # This is the main identifier for each test registry entry
                # It links to the ReadingTest.test_id field
                ('test_id', models.UUIDField(
                    primary_key=True,  # This field is the primary key
                    help_text="Unique identifier for the test (links to ReadingTest.test_id)"
                )),
                
                # =============================================================================
                # BASIC INFORMATION FIELDS
                # =============================================================================
                # Human-readable name for the test (e.g., "Cambridge IELTS 15 Test 1")
                ('test_name', models.CharField(
                    max_length=255,  # Maximum 255 characters
                    help_text="Human-readable name for the test (e.g., 'Cambridge IELTS 15 Test 1')"
                )),
                
                # Organization ID for multi-tenant support
                ('organization_id', models.IntegerField(
                    help_text="Organization ID that owns this test (for multi-tenant isolation)"
                )),
                
                # =============================================================================
                # STATUS CONTROL FIELDS
                # =============================================================================
                # Whether this test is currently available for students
                ('is_active', models.BooleanField(
                    default=True,  # New tests are active by default
                    help_text="Whether this test is currently available for students (True=active, False=disabled)"
                )),
                
                # Whether this test is featured/premium
                ('is_featured', models.BooleanField(
                    default=False,  # Most tests are not featured by default
                    help_text="Whether this is a featured/premium test (for future premium features)"
                )),
                
                # =============================================================================
                # USAGE TRACKING FIELDS
                # =============================================================================
                # How many times this test has been assigned to students
                ('usage_count', models.IntegerField(
                    default=0,  # Start at 0 when test is first registered
                    help_text="Number of times this test has been assigned to students (for load balancing)"
                )),
                
                # When this test was last assigned to a student
                ('last_used', models.DateTimeField(
                    auto_now=True,  # Automatically update whenever record is saved
                    help_text="When this test was last assigned to a student (for rotation)"
                )),
                
                # =============================================================================
                # TIMESTAMP FIELDS
                # =============================================================================
                # When this test was first registered in the system
                ('created_at', models.DateTimeField(
                    auto_now_add=True,  # Set automatically when record is first created
                    help_text="When this test was first registered in the system"
                )),
                
                # When this test was last modified (any field changed)
                ('updated_at', models.DateTimeField(
                    auto_now=True,  # Automatically update whenever any field changes
                    help_text="When this test was last modified (any field changed)"
                )),
                
                # =============================================================================
                # FUTURE-READY FIELDS
                # =============================================================================
                # Test category (Academic, General Training, etc.)
                ('test_category', models.CharField(
                    max_length=50,  # Maximum 50 characters
                    default='Academic',  # Default to Academic IELTS
                    help_text="Test category (Academic, General Training, etc.)"
                )),
                
                # Difficulty level (Easy, Medium, Hard)
                ('difficulty_level', models.CharField(
                    max_length=20,  # Maximum 20 characters
                    default='Medium',  # Default to Medium difficulty
                    help_text="Difficulty level (Easy, Medium, Hard) for adaptive selection"
                )),
                
                # Target band score (6.0, 7.0, 8.0, etc.)
                ('target_band_score', models.CharField(
                    max_length=10,  # Maximum 10 characters (e.g., "7.5")
                    default='7.0',  # Default to Band 7.0
                    help_text="Target band score for this test (e.g., '7.0', '8.5')"
                )),
                
                # Rotation priority (higher number = higher priority)
                ('rotation_priority', models.IntegerField(
                    default=0,  # Default priority (0 = normal priority)
                    help_text="Rotation priority (higher number = selected first, 0 = normal priority)"
                )),
            ],
            
            # =============================================================================
            # MODEL META OPTIONS
            # =============================================================================
            # These options configure how Django handles the model
            # =============================================================================
            options={
                # Custom table name in database (instead of default 'reading_testregistry')
                'db_table': 'test_registry',
                
                # Default ordering when querying records
                # Order: high priority first, then least used, then oldest
                'ordering': ['-rotation_priority', 'usage_count', 'last_used'],
                
                # Human-readable names for Django admin
                'verbose_name': 'Test Registry Entry',
                'verbose_name_plural': 'Test Registry Entries',
            },
        ),
        
        # =============================================================================
        # CREATE DATABASE INDEXES
        # =============================================================================
        # These indexes improve query performance for common operations
        # =============================================================================
        
        # Index on organization_id for fast filtering by organization
        # This is used when getting tests for a specific organization
        migrations.AddIndex(
            model_name='testregistry',
            index=models.Index(
                fields=['organization_id'],  # Index on this field
                name='test_registry_org_idx'  # Name of the index in database
            ),
        ),
        
        # Index on is_active for fast filtering of active tests
        # This is used when getting only active tests
        migrations.AddIndex(
            model_name='testregistry',
            index=models.Index(
                fields=['is_active'],  # Index on this field
                name='test_registry_active_idx'  # Name of the index in database
            ),
        ),
        
        # Index on usage_count for fast load balancing queries
        # This is used when selecting tests with lowest usage
        migrations.AddIndex(
            model_name='testregistry',
            index=models.Index(
                fields=['usage_count'],  # Index on this field
                name='test_registry_usage_idx'  # Name of the index in database
            ),
        ),
        
        # Composite index for common queries (organization + active status)
        # This is used when getting active tests for a specific organization
        migrations.AddIndex(
            model_name='testregistry',
            index=models.Index(
                fields=['organization_id', 'is_active'],  # Index on both fields
                name='test_registry_org_active_idx'  # Name of the index in database
            ),
        ),
        
        # Composite index for load balancing queries (active + usage + last_used)
        # This is used when selecting the best test for load balancing
        migrations.AddIndex(
            model_name='testregistry',
            index=models.Index(
                fields=['is_active', 'usage_count', 'last_used'],  # Index on three fields
                name='test_registry_balancing_idx'  # Name of the index in database
            ),
        ),
    ]
