from django.core.management.base import BaseCommand
from ...services import PipelineService

class Command(BaseCommand):

    def handle(self, *args, **options):
        PipelineService().start_pipeline()
        #self.stdout.write(self.style.SUCCESS("A pipeline folyamat sikeresen lefutott!"))
