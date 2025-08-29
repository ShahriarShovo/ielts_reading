from django.apps import AppConfig


class ReadingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reading'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This ensures that signals are registered when Django starts.
        """
        import reading.signals
