import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/app_colors.dart';
import '../theme/app_motion.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';

/// Segmented physical toggle pill to switch between Standard Camera View and A-Eye Dark Mode.
class ModeSwitchPill extends StatelessWidget {
  final bool isAEyeMode;
  final ValueChanged<bool> onModeChanged;

  const ModeSwitchPill({
    super.key,
    required this.isAEyeMode,
    required this.onModeChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: isAEyeMode ? 'A-Eye Dark Screen Mode selected' : 'Visual Camera Mode selected',
      hint: 'Double tap to toggle between camera view and dark screen mode',
      button: true,
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: AppColors.surfaceElevated,
          borderRadius: AppSpacing.roundedPill,
          border: Border.all(color: AppColors.borderHairline, width: 1),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(
              child: _ModeSegment(
                icon: Icons.visibility_rounded,
                label: 'Visual',
                isSelected: !isAEyeMode,
                onTap: () {
                  if (isAEyeMode) {
                    HapticFeedback.selectionClick();
                    onModeChanged(false);
                  }
                },
              ),
            ),
            const SizedBox(width: 4),
            Flexible(
              child: _ModeSegment(
                icon: Icons.dark_mode_rounded,
                label: 'A-Eye Dark',
                isSelected: isAEyeMode,
                onTap: () {
                  if (!isAEyeMode) {
                    HapticFeedback.selectionClick();
                    onModeChanged(true);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ModeSegment extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _ModeSegment({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: AppMotion.getDuration(context, AppMotion.quick),
      curve: AppMotion.expressiveOut,
      decoration: BoxDecoration(
        color: isSelected ? AppColors.surfaceCard : Colors.transparent,
        borderRadius: AppSpacing.roundedPill,
        border: Border.all(
          color: isSelected ? AppColors.primary.withValues(alpha: 0.5) : Colors.transparent,
          width: 1,
        ),
        boxShadow: isSelected
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.25),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: AppSpacing.roundedPill,
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 16,
                  color: isSelected ? AppColors.primary : AppColors.textMuted,
                ),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: AppTypography.labelSmall.copyWith(
                      color: isSelected ? AppColors.textPrimary : AppColors.textMuted,
                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
