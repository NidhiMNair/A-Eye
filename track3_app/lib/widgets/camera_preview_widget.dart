import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../camera/camera_service.dart';

/// Renders the hardware camera preview when active, or a clean accessible placeholder.
class CameraPreviewWidget extends StatelessWidget {
  final CameraService cameraService;
  final bool isAssistanceActive;

  const CameraPreviewWidget({
    super.key,
    required this.cameraService,
    required this.isAssistanceActive,
  });

  @override
  Widget build(BuildContext context) {
    final controller = cameraService.controller;

    return AspectRatio(
      aspectRatio: 4 / 3,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Container(
          color: Colors.black,
          child: (isAssistanceActive && controller != null && controller.value.isInitialized)
              ? CameraPreview(controller)
              : Semantics(
                  label: 'Camera is currently inactive',
                  child: const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.videocam_off, size: 48, color: Colors.white54),
                        SizedBox(height: 8),
                        Text(
                          'Camera Inactive',
                          style: TextStyle(color: Colors.white70, fontSize: 16),
                        ),
                      ],
                    ),
                  ),
                ),
        ),
      ),
    );
  }
}
