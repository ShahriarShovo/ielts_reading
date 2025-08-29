from django.core.management.base import BaseCommand
from reading.models import ReadingTest, TestRegistry

class Command(BaseCommand):
    help = 'Register all existing ReadingTest records in TestRegistry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Register tests for specific organization ID only'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-registration even if already registered'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 REGISTERING EXISTING TESTS IN TEST REGISTRY')
        )
        
        # Get tests to register
        if options['organization']:
            tests = ReadingTest.objects.filter(organization_id=options['organization'])
            self.stdout.write(f"📊 Registering tests for organization {options['organization']}")
        else:
            tests = ReadingTest.objects.all()
            self.stdout.write(f"📊 Registering all tests")
        
        self.stdout.write(f"📋 Found {tests.count()} tests to process")
        
        registered_count = 0
        updated_count = 0
        skipped_count = 0
        
        for test in tests:
            try:
                # Check if already registered
                existing_registry = TestRegistry.objects.filter(
                    test_id=test.test_id
                ).first()
                
                if existing_registry and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(f"⏭️  Test {test.test_id} already registered, skipping...")
                    )
                    skipped_count += 1
                    continue
                
                # No metadata needed for TestRegistry
                pass
                
                if existing_registry and options['force']:
                    # Update existing registry
                    existing_registry.test_name = test.test_name
                    existing_registry.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Updated TestRegistry for test {test.test_id}")
                    )
                    updated_count += 1
                else:
                    # Create new registry entry
                    TestRegistry.objects.create(
                        test_id=test.test_id,
                        test_name=test.test_name,
                        organization_id=test.organization_id,
                        is_active=True,
                        test_category='Academic',
                        difficulty_level='Medium',
                        target_band_score='7.0',
                        rotation_priority=0
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Registered test {test.test_id} for organization {test.organization_id}")
                    )
                    registered_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to register test {test.test_id}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📊 REGISTRATION SUMMARY"))
        self.stdout.write("="*50)
        self.stdout.write(f"✅ Newly registered: {registered_count}")
        self.stdout.write(f"🔄 Updated: {updated_count}")
        self.stdout.write(f"⏭️  Skipped: {skipped_count}")
        self.stdout.write(f"📋 Total processed: {registered_count + updated_count + skipped_count}")
        
        # Check final status
        total_registry = TestRegistry.objects.count()
        self.stdout.write(f"\n📊 Total TestRegistry entries: {total_registry}")
        
        if options['organization']:
            org_registry = TestRegistry.objects.filter(organization_id=options['organization']).count()
            self.stdout.write(f"📊 TestRegistry entries for organization {options['organization']}: {org_registry}")
        
        self.stdout.write(
            self.style.SUCCESS("\n🎯 Registration process completed!")
        )
