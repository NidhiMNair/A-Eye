import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../camera/camera_service.dart';
import '../models/track2_result.dart';
import '../theme/app_colors.dart';
import '../theme/app_motion.dart';
import '../theme/app_spacing.dart';

/// A production-grade, undistorted portrait camera viewport.
/// - Displays 3:4 or taller portrait feed without stretching
/// - Shimmer placeholder with smooth cross-fade reveal
/// - Optional Developer Mode spatial overlay (central zone, hazards)
class CameraViewport extends StatelessWidget {
  final CameraService cameraService;
  final bool isAssistanceActive;
  final bool isDeveloperMode;
  final Track2Result? latestResult;
  final double? targetAspectRatio;

  const CameraViewport({
    super.key,
    required this.cameraService,
    required this.isAssistanceActive,
    this.isDeveloperMode = false,
    this.latestResult,
    this.targetAspectRatio = 3 / 4,
  });

  @override
  Widget build(BuildContext context) {
    final controller = cameraService.controller;
    final isReady = isAssistanceActive && controller != null && controller.value.isInitialized;

    // Calculate real portrait aspect ratio (Android sensors report landscape width > height)
    double effectiveRatio = targetAspectRatio ?? (3 / 4);
    if (isReady) {
      final sensorRatio = controller.value.aspectRatio;
      effectiveRatio = sensorRatio > 1.0 ? (1.0 / sensorRatio) : sensorRatio;
    }

    return AspectRatio(
      aspectRatio: effectiveRatio,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: AppSpacing.roundedXl,
          border: Border.all(color: AppColors.borderHairline, width: 1.5),
          boxShadow: const [
            BoxShadow(
              color: Color(0x66000000),
              blurRadius: 24,
              offset: Offset(0, 8),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: AppSpacing.roundedXl,
          child: Stack(
            fit: StackFit.expand,
            children: [
              // 1. Shimmer/Placeholder surface
              Container(
                color: AppColors.surfaceElevated,
                child: const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.camera_alt_outlined, size: 44, color: AppColors.textMuted),
                      SizedBox(height: AppSpacing.xs),
                      Text(
                        'Sensors Ready',
                        style: TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // 2. Animated Live Camera Feed
              AnimatedOpacity(
                opacity: isReady ? 1.0 : 0.0,
                duration: AppMotion.getDuration(context, AppMotion.standard),
                curve: AppMotion.expressiveOut,
                child: isReady
                    ? FittedBox(
                        fit: BoxFit.cover,
                        child: SizedBox(
                          width: controller.value.previewSize?.height ?? 720,
                          height: controller.value.previewSize?.width ?? 960,
                          child: CameraPreview(controller),
                        ),
                      )
                    : const SizedBox.shrink(),
              ),

              // 3. Subtle Vignette Depth Layer
              IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: RadialGradient(
                      center: Alignment.center,
                      radius: 1.1,
                      colors: [
                        Colors.transparent,
                        Colors.black.withValues(alpha: 0.35),
                      ],
                    ),
                  ),
                ),
              ),

              // 4. Developer Mode Telemetry Overlays (Spatial zones & hazards)
              if (isReady && isDeveloperMode && latestResult != null)
                _DeveloperSpatialOverlay(result: latestResult!),
            ],
          ),
        ),
      ),
    );
  }
}

/// Developer mode visual grid overlay showing Track 2 spatial zones and hazard items.
class _DeveloperSpatialOverlay extends StatelessWidget {
  final Track2Result result;

  const _DeveloperSpatialOverlay({required this.result});

  @override
  Widget build(BuildContext context) {
    final hasHazard = result.decision.category.name.toLowerCase().contains('alert');

    return IgnorePointer(
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Central focal corridor lines
          Row(
            children: [
              Expanded(
                flex: 1,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border(right: BorderSide(color: Colors.white.withValues(alpha: 0.15), width: 1)),
                  ),
                ),
              ),
              Expanded(
                flex: 2,
                child: Container(
                  decoration: BoxDecoration(
                    color: hasHazard ? Colors.red.withValues(alpha: 0.08) : Colors.teal.withValues(alpha: 0.04),
                    border: Border.all(
                      color: hasHazard ? Colors.redAccent.withValues(alpha: 0.4) : Colors.tealAccent.withValues(alpha: 0.3),
                      width: 1.5,
                    ),
                  ),
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: Container(
                      margin: const EdgeInsets.only(top: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        hasHazard ? 'CENTRAL HAZARD ZONE' : 'CENTRAL PATH',
                        style: TextStyle(
                          color: hasHazard ? Colors.redAccent : Colors.tealAccent,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              Expanded(
                flex: 1,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border(left: BorderSide(color: Colors.white.withValues(alpha: 0.15), width: 1)),
                  ),
                ),
              ),
            ],
          ),

          // Track 2 Detected Items HUD in bottom corner
          Positioned(
            left: 12,
            bottom: 12,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.75),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white24, width: 0.8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'FRAME: ${result.frameId.substring(0, 8.clamp(0, result.frameId.length))}',
                    style: const TextStyle(color: Colors.white70, fontSize: 10, fontFamily: 'monospace'),
                  ),
                  if (result.perception.hazards.isNotEmpty)
                    Text(
                      'HAZARDS: ${result.perception.hazards.join(", ")}',
                      style: const TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
