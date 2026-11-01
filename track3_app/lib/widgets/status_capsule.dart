import 'dart:ui';
import 'package:flutter/material.dart';

import '../presentation/display_text_formatter.dart';
import '../state/session_state.dart';
import '../theme/app_colors.dart';
import '../theme/app_motion.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';

/// Floating frosted glass status capsule providing calm, human feedback.
/// Replaces developer jargon ("PROCESSING", "Inference complete") with glanceable human clarity.
class StatusCapsule extends StatelessWidget {
  final SessionState state;

  const StatusCapsule({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final status = state.status;
    final isOnline = state.isBackendOnline;
    final isSpeaking = status == AssistanceStatus.speaking;
    final isInferring = state.schedulerStats?.isCurrentlyInferring ?? false;
    final hasError = status == AssistanceStatus.error || !isOnline;

    final humanTitle = DisplayTextFormatter.formatStatusTitle(
      isSpeaking: isSpeaking,
      isInferring: isInferring,
      hasError: hasError,
      isOnline: isOnline,
      categoryDisplay: state.latestResult?.decision.category.name,
    );

    // Pick semantic indicator color & icon (never color alone)
    Color accentColor;
    IconData statusIcon;

    if (!isOnline || status == AssistanceStatus.error) {
      accentColor = AppColors.hazard;
      statusIcon = Icons.wifi_off_rounded;
    } else if (isSpeaking) {
      accentColor = AppColors.guidance;
      statusIcon = Icons.volume_up_rounded;
    } else if (isInferring || status == AssistanceStatus.cameraReady) {
      accentColor = AppColors.primary;
      statusIcon = Icons.lens_blur_rounded;
    } else {
      accentColor = AppColors.textMuted;
      statusIcon = Icons.radio_button_checked_rounded;
    }

    final semanticAnnouncement = 'Status: $humanTitle. ${state.statusMessage}';

    return Semantics(
      liveRegion: true,
      label: semanticAnnouncement,
      child: ClipRRect(
        borderRadius: AppSpacing.roundedPill,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: AppSpacing.glassBlurSigma, sigmaY: AppSpacing.glassBlurSigma),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.surfaceGlass,
              borderRadius: AppSpacing.roundedPill,
              border: Border.all(
                color: accentColor.withValues(alpha: 0.35),
                width: 1.2,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.2),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Pulse dot / icon
                AnimatedContainer(
                  duration: AppMotion.getDuration(context, AppMotion.quick),
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: accentColor,
                    boxShadow: [
                      BoxShadow(
                        color: accentColor.withValues(alpha: 0.6),
                        blurRadius: 8,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: AppSpacing.xs + 2),

                Icon(statusIcon, size: 16, color: accentColor),
                const SizedBox(width: AppSpacing.xs),

                // Human Title
                Flexible(
                  child: Text(
                    humanTitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTypography.labelMedium.copyWith(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),

                if (!isOnline) ...[
                  const SizedBox(width: AppSpacing.xs),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.hazard.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      'OFFLINE',
                      style: AppTypography.labelSmall.copyWith(
                        color: AppColors.hazard,
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
