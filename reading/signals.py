from django.db.models.signals import post_save
from django.dispatch import receiver
from reading.models import ReadingTest, TestRegistry, QuestionType

@receiver(post_save, sender=ReadingTest)
def auto_register_test_in_registry(sender, instance, created, **kwargs):
    """
    Automatically register a ReadingTest in TestRegistry when it's created.
    
    This signal ensures that every new ReadingTest is automatically
    available for student exams without manual intervention.
    
    Args:
        sender: The ReadingTest model class
        instance: The ReadingTest instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Only register new tests, not updates
        try:
            # Check if already registered
            existing_registry = TestRegistry.objects.filter(
                test_id=instance.test_id
            ).first()
            
            if not existing_registry:
                # Create new registry entry
                TestRegistry.objects.create(
                    test_id=instance.test_id,
                    test_name=instance.test_name,
                    organization_id=instance.organization_id,
                    is_active=True,
                    test_category='Academic',
                    difficulty_level='Medium',
                    target_band_score='7.0',
                    rotation_priority=0
                )
                print(f"✅ Auto-registered test {instance.test_id} in TestRegistry")
            else:
                print(f"ℹ️  Test {instance.test_id} already registered in TestRegistry")
                
        except Exception as e:
            print(f"❌ Failed to auto-register test {instance.test_id}: {str(e)}")

@receiver(post_save, sender=ReadingTest)
def update_test_registry_on_test_update(sender, instance, created, **kwargs):
    """
    Update TestRegistry when ReadingTest is updated.
    
    This ensures that any changes to the test (title, status, etc.)
    are reflected in the TestRegistry.
    
    Args:
        sender: The ReadingTest model class
        instance: The ReadingTest instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if not created:
        # Only update existing tests, not new ones
        try:
            # Find existing registry entry
            registry = TestRegistry.objects.filter(
                test_id=instance.test_id
            ).first()
            
            if registry:
                # Update test information
                registry.test_name = instance.test_name
                registry.save()
                print(f"✅ Updated TestRegistry for test {instance.test_id}")
                
        except Exception as e:
            print(f"❌ Failed to update TestRegistry for test {instance.test_id}: {str(e)}")

@receiver(post_save, sender=QuestionType)
def ensure_test_registered_when_question_created(sender, instance, created, **kwargs):
    """
    Ensure the test is registered in TestRegistry when questions are created.
    
    This signal ensures that even if a test wasn't automatically registered
    when created, it gets registered when the first question is added.
    
    Args:
        sender: The QuestionType model class
        instance: The QuestionType instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        try:
            # Get the test through the passage
            test = instance.passage.test
            
            # Check if test is already registered
            existing_registry = TestRegistry.objects.filter(
                test_id=test.test_id
            ).first()
            
            if not existing_registry:
                # Register the test
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
                print(f"✅ Auto-registered test {test.test_id} via question creation")
            else:
                # Test already registered, no need to update anything
                pass
                print(f"✅ Updated TestRegistry for test {test.test_id} after question creation")
                
        except Exception as e:
            print(f"❌ Failed to ensure test registration via question: {str(e)}")
