import 'package:flutter/material.dart';

import '../state/session_state.dart';
import '../theme/app_colors.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';

/// Developer HUD modal sheet revealing telemetry, frame scheduler stats,
/// and raw Track 2 perception contracts for sighted engineers and testers.
class DeveloperTelemetrySheet extends StatelessWidget {
  final SessionState state;
  final String backendUrl;

  const DeveloperTelemetrySheet({
    super.key,
    required this.state,
    required this.backendUrl,
  });

  static void show(BuildContext context, {required SessionState state, required String backendUrl}) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (_) => DeveloperTelemetrySheet(state: state, backendUrl: backendUrl),
    );
  }

  @override
  Widget build(BuildContext context) {
    final stats = state.schedulerStats;
    final latestResult = state.latestResult;

    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: BorderRadius.vertical(top: AppSpacing.radiusXl),
      ),
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle bar
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Developer Telemetry HUD', style: AppTypography.headlineMedium),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    state.backendMode.toUpperCase(),
                    style: AppTypography.labelSmall.copyWith(color: AppColors.primary, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),

            // Performance metrics grid
            Row(
              children: [
                _StatTile(
                  label: 'LATENCY',
                  value: '${stats?.lastLatencyMs ?? 0} ms',
                  color: AppColors.info,
                ),
                const SizedBox(width: AppSpacing.sm),
                _StatTile(
                  label: 'PROCESSED',
                  value: '${stats?.processedFrames ?? 0}',
                  color: AppColors.primary,
                ),
                const SizedBox(width: AppSpacing.sm),
                _StatTile(
                  label: 'DROPPED',
                  value: '${stats?.droppedFrames ?? 0}',
                  color: (stats?.droppedFrames ?? 0) > 10 ? AppColors.guidance : AppColors.textMuted,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),

            // Backend URL
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surfaceCard,
                borderRadius: AppSpacing.roundedSm,
                border: Border.all(color: AppColors.borderHairline),
              ),
              child: Row(
                children: [
                  const Icon(Icons.lan_outlined, size: 18, color: AppColors.textMuted),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      backendUrl,
                      style: AppTypography.telemetry.copyWith(color: AppColors.textPrimary),
                    ),
                  ),
                  Icon(
                    state.isBackendOnline ? Icons.check_circle : Icons.error_outline,
                    size: 16,
                    color: state.isBackendOnline ? AppColors.safeNeutral : AppColors.hazard,
                  ),
                ],
              ),
            ),

            if (latestResult != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text('RAW PERCEPTION DECISION', style: AppTypography.labelSmall.copyWith(letterSpacing: 1.1)),
              const SizedBox(height: 6),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.5),
                  borderRadius: AppSpacing.roundedSm,
                  border: Border.all(color: AppColors.borderHairline),
                ),
                child: Text(
                  'Message: ${latestResult.decision.message}\n'
                  'Category: ${latestResult.decision.category.name}\n'
                  'Priority: ${latestResult.decision.priority.name}\n'
                  'Hazards: ${latestResult.perception.hazards.join(", ")}\n'
                  'FrameId: ${latestResult.frameId}',
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: Colors.white70, height: 1.4),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatTile({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: AppSpacing.roundedMd,
          border: Border.all(color: AppColors.borderHairline),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: AppTypography.labelSmall.copyWith(fontSize: 10, color: AppColors.textMuted)),
            const SizedBox(height: 4),
            Text(value, style: AppTypography.labelLarge.copyWith(color: color, fontSize: 16)),
          ],
        ),
      ),
    );
  }
}
