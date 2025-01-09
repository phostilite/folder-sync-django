# folder_sync/models.py
from django.db import models

class SyncConfiguration(models.Model):
    name = models.CharField(max_length=255)
    main_folder = models.CharField(max_length=1000)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.main_folder}"

class TargetFolder(models.Model):
    sync_config = models.ForeignKey(SyncConfiguration, on_delete=models.CASCADE, related_name='target_folders')
    path = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.path