from django.core.management.base import BaseCommand
from pandasai_app.models import initialize_model_data

class Command(BaseCommand):
    help = 'Initialize AI model data'

    def handle(self, *args, **kwargs):
        initialize_model_data()
        self.stdout.write(self.style.SUCCESS('Successfully initialized AI model data'))