from django.core.management.base import BaseCommand
from reading.models import ReadingTest, Passage
import uuid

class Command(BaseCommand):
    help = 'Create test data for the reading module'

    def handle(self, *args, **options):
        # Create a test
        test = ReadingTest.objects.create(
            test_name="Cambridge IELTS 18 Academic",
            source="Cambridge IELTS 18",
            organization_id="1"  # Use the organization ID from your user
        )
        
        self.stdout.write(f"Created test: {test.test_name} with ID: {test.test_id}")
        
        # Create a passage for the test
        passage = Passage.objects.create(
            test=test,
            title="The History of Coffee",
            instruction="You should spend about 20 minutes on Questions 1-13, which are based on Reading Passage 1 below.",
            text="Coffee is a brewed drink prepared from roasted coffee beans, the seeds of berries from certain Coffea species. The genus Coffea is native to tropical Africa and Madagascar, the Comoros, Mauritius, and Réunion in the Indian Ocean. Coffee plants are now cultivated in over 70 countries, primarily in the equatorial regions of the Americas, Southeast Asia, the Indian subcontinent, and Africa. The two most commonly grown are C. arabica and C. robusta. Once ripe, coffee berries are picked, processed, and dried. Dried coffee seeds are roasted to varying degrees, depending on the desired flavor. Roasted beans are ground and then brewed with near-boiling water to produce the beverage known as coffee.",
            order=1,
            organization_id="1"
        )
        
        self.stdout.write(f"Created passage: {passage.title} with ID: {passage.passage_id}")
        
        # Create a second passage
        passage2 = Passage.objects.create(
            test=test,
            title="The Benefits of Exercise",
            instruction="You should spend about 20 minutes on Questions 14-26, which are based on Reading Passage 2 below.",
            text="Regular physical activity is one of the most important things you can do for your health. Being physically active can improve your brain health, help manage weight, reduce the risk of disease, strengthen bones and muscles, and improve your ability to do everyday activities. Adults who sit less and do any amount of moderate-to-vigorous physical activity gain some health benefits. Only a few lifestyle choices have as large an impact on your health as physical activity. Everyone can experience the health benefits of physical activity – age, abilities, ethnicity, shape, or size do not matter.",
            order=2,
            organization_id=1
        )
        
        self.stdout.write(f"Created passage: {passage2.title} with ID: {passage2.passage_id}")
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created test data!')
        )
