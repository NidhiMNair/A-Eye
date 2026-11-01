import 'dart:ui';
import 'package:flutter/material.dart';

import '../models/assistance_category.dart';
import '../presentation/display_text_formatter.dart';
import '../state/session_state.dart';
import '../theme/app_colors.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';
import 'severity_badge.dart';

/// Floating frosted glass guidance card.
/// Cleans punctuation via DisplayTextFormatter, displays non-color SeverityBadge,
/// and isolates developer telemetry strictly behind the Developer Mode toggle.
class GuidanceSheet extends StatelessWidget {
  final SessionState state;
  final bool isDeveloperMode;
  final VoidCallback? onReplaySpeech;

  const GuidanceSheet({
    super.key,
    required this.state,
    this.isDeveloperMode = false,
    this.onReplaySpeech,
  });

  @override
  Widget build(BuildContext context) {
    final latestResult = state.latestResult;
    final rawMessage = state.lastSpokenMessage.isNotEmpty
        ? state.lastSpokenMessage
        : (latestResult != null ? latestResult.decision.message : 'A-Eye is standing by.');

    // Clean stray punctuation (e.g. ".,") strictly for display
    final displayMessage = DisplayTextFormatter.formatGuidance(rawMessage);
    final category = latestResult?.decision.category ?? AssistanceCategory.none;

    return ClipRRect(
      borderRadius: AppSpacing.roundedXl,
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: AppSpacing.glassBlurSigma, sigmaY: AppSpacing.glassBlurSigma),
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            color: AppColors.surfaceGlass,
            borderRadius: AppSpacing.roundedXl,
            border: Border.all(color: AppColors.borderHairline, width: 1.2),
            boxShadow: const [
              BoxShadow(
                color: Color(0x66000000),
                blurRadius: 20,
                offset: Offset(0, 6),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Header: Severity badge + Replay audio button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  SeverityBadge(category: category),
                  if (onReplaySpeech != null && state.lastSpokenMessage.isNotEmpty)
                    IconButton(
                      icon: const Icon(Icons.replay_rounded, size: 20, color: AppColors.primary),
                      tooltip: 'Repeat guidance voice',
                      onPressed: onReplaySpeech,
                      style: IconButton.styleFrom(
                        backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                        padding: const EdgeInsets.all(6),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),

              // Main spoken guidance text (Lexend body large for optimal visual acuity)
              Semantics(
                label: 'Guidance: $displayMessage',
                child: Text(
                  displayMessage,
                  style: AppTypography.titleLarge.copyWith(
                    color: AppColors.textPrimary,
                    fontSize: 17,
                    height: 1.45,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),

              // Telemetry bar: Strictly isolated to Developer Mode
              if (isDeveloperMode && state.schedulerStats != null) ...[
                const SizedBox(height: AppSpacing.md),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.4),
                    borderRadius: AppSpacing.roundedSm,
                    border: Border.all(color: AppColors.borderHairline, width: 0.8),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'FPS: ${(1000 / (state.schedulerStats!.lastLatencyMs.clamp(1, 10000))).toStringAsFixed(1)}',
                        style: AppTypography.telemetry.copyWith(color: AppColors.primary),
                      ),
                      Text(
                        'Dropped: ${state.schedulerStats!.droppedFrames}',
                        style: AppTypography.telemetry.copyWith(
                          color: state.schedulerStats!.droppedFrames > 10 ? AppColors.guidance : AppColors.textMuted,
                        ),
                      ),
                      Text(
                        'Latency: ${state.schedulerStats!.lastLatencyMs}ms',
                        style: AppTypography.telemetry.copyWith(color: AppColors.info),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
