# folder_sync/views.py
from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib import messages
from .models import SyncConfiguration, TargetFolder
from .sync_engine import FolderSyncEngine
import os
import logging

logger = logging.getLogger(__name__)

sync_engine = FolderSyncEngine()

class SyncConfigurationView(View):
    template_name = 'folder_sync/configuration.html'

    def get(self, request):
        configs = SyncConfiguration.objects.all()
        return render(request, self.template_name, {'configs': configs})

    def validate_folder_path(self, path):
        if not os.path.exists(path):
            raise ValueError(f"Folder does not exist: {path}")
        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")
        return os.path.abspath(path)

    def post(self, request):
        action = request.POST.get('action')
        logger.info(f"Received POST request with action: {action}")
        
        if action == 'create':
            try:
                name = request.POST.get('name')
                main_folder = request.POST.get('main_folder')
                target_folders = request.POST.getlist('target_folders')
                
                logger.info(f"Creating new sync configuration: {name}")
                logger.info(f"Main folder: {main_folder}")
                logger.info(f"Target folders: {target_folders}")

                # Validate paths
                main_folder = self.validate_folder_path(main_folder)
                validated_targets = [self.validate_folder_path(t) for t in target_folders]
                logger.debug("All paths validated successfully")

                # Create configuration
                config = SyncConfiguration.objects.create(
                    name=name,
                    main_folder=main_folder
                )
                logger.info(f"Created sync configuration with ID: {config.id}")

                for target in validated_targets:
                    TargetFolder.objects.create(
                        sync_config=config,
                        path=target
                    )
                    logger.debug(f"Added target folder: {target}")

                messages.success(request, 'Configuration created successfully')
                logger.info("Configuration creation completed successfully")

            except ValueError as e:
                logger.error(f"Validation error during configuration creation: {str(e)}")
                messages.error(request, str(e))
            except Exception as e:
                logger.exception("Unexpected error during configuration creation")
                messages.error(request, f'Error creating configuration: {str(e)}')

        elif action == 'start':
            config_id = request.POST.get('config_id')
            logger.info(f"Starting sync for configuration ID: {config_id}")
            
            try:
                config = SyncConfiguration.objects.get(id=config_id)
                target_paths = [t.path for t in config.target_folders.all()]
                
                logger.info(f"Starting sync process for {config.name}")
                logger.info(f"Main folder: {config.main_folder}")
                logger.info(f"Target folders: {target_paths}")
                
                sync_engine.start_sync(config.main_folder, target_paths)
                config.is_active = True
                config.save()
                
                messages.success(request, 'Sync started successfully')
                logger.info(f"Sync started successfully for configuration: {config.name}")
                
            except Exception as e:
                logger.exception(f"Error starting sync for configuration {config_id}")
                messages.error(request, f'Error starting sync: {str(e)}')

        elif action == 'stop':
            config_id = request.POST.get('config_id')
            logger.info(f"Stopping sync for configuration ID: {config_id}")
            
            try:
                config = SyncConfiguration.objects.get(id=config_id)
                sync_engine.stop_sync()
                config.is_active = False
                config.save()
                
                messages.success(request, 'Sync stopped successfully')
                logger.info(f"Sync stopped successfully for configuration: {config.name}")
                
            except Exception as e:
                logger.exception(f"Error stopping sync for configuration {config_id}")
                messages.error(request, f'Error stopping sync: {str(e)}')

        return redirect('sync_configuration')