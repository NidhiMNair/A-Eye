import 'package:flutter/material.dart';

import '../models/assistance_category.dart';
import '../theme/app_colors.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';

/// Accessible severity indicator that never relies on color alone.
/// Employs distinct shape, icon, and explicit text semantics for every state.
class SeverityBadge extends StatelessWidget {
  final AssistanceCategory category;

  const SeverityBadge({super.key, required this.category});

  @override
  Widget build(BuildContext context) {
    Color badgeColor;
    Color containerColor;
    IconData badgeIcon;
    String labelText;
    BorderRadius badgeRadius;

    switch (category) {
      case AssistanceCategory.alert:
        badgeColor = AppColors.hazard;
        containerColor = AppColors.hazardContainer;
        badgeIcon = Icons.warning_rounded;
        labelText = 'HAZARD';
        badgeRadius = BorderRadius.circular(6); // Sharper angled corners
        break;
      case AssistanceCategory.guidance:
        badgeColor = AppColors.guidance;
        containerColor = AppColors.guidanceContainer;
        badgeIcon = Icons.navigation_rounded;
        labelText = 'GUIDANCE';
        badgeRadius = BorderRadius.circular(10); // Rounded squircle
        break;
      case AssistanceCategory.info:
        badgeColor = AppColors.info;
        containerColor = AppColors.infoContainer;
        badgeIcon = Icons.info_outline_rounded;
        labelText = 'AWARENESS';
        badgeRadius = AppSpacing.roundedPill; // Full pill
        break;
      case AssistanceCategory.none:
      case AssistanceCategory.unknown:
        badgeColor = AppColors.textMuted;
        containerColor = AppColors.surfaceElevated;
        badgeIcon = Icons.check_circle_outline_rounded;
        labelText = 'CLEAR';
        badgeRadius = AppSpacing.roundedSm;
        break;
    }

    return Semantics(
      label: 'Severity level: $labelText',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: containerColor,
          borderRadius: badgeRadius,
          border: Border.all(color: badgeColor.withValues(alpha: 0.6), width: 1.2),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(badgeIcon, size: 14, color: badgeColor),
            const SizedBox(width: 5),
            Text(
              labelText,
              style: AppTypography.labelSmall.copyWith(
                color: badgeColor,
                fontSize: 10,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.8,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
