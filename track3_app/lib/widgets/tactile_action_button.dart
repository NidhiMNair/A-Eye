import 'package:flutter/material.dart';

import '../state/session_state.dart';
import '../theme/app_colors.dart';
import '../theme/app_motion.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';

/// A production-grade tactile primary action control with spring morphing
/// and an animated listening aura for visually impaired and low-vision accessibility.
///
/// Distinctly avoids generic flat red slabs. Red is reserved strictly for real hazards.
class TactileActionButton extends StatefulWidget {
  final AssistanceStatus status;
  final VoidCallback onStart;
  final VoidCallback onStop;

  const TactileActionButton({
    super.key,
    required this.status,
    required this.onStart,
    required this.onStop,
  });

  @override
  State<TactileActionButton> createState() => _TactileActionButtonState();
}

class _TactileActionButtonState extends State<TactileActionButton> with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: AppMotion.auraBreathing,
    )..repeat();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isActive = widget.status.isActive;
    final isBusy = widget.status == AssistanceStatus.starting || widget.status == AssistanceStatus.stopping;
    final isSpeaking = widget.status == AssistanceStatus.speaking;

    final disableAnimations = MediaQuery.of(context).disableAnimations;

    final label = isActive ? 'PAUSE ASSISTANCE' : 'START ASSISTANCE';
    final semanticHint = isActive
        ? 'Double tap to pause camera guidance.'
        : 'Double tap to start camera scanning and receive continuous audio assistance.';

    return Semantics(
      button: true,
      enabled: !isBusy,
      label: label,
      hint: semanticHint,
      child: AnimatedBuilder(
        animation: _pulseController,
        builder: (context, child) {
          final pulseValue = disableAnimations ? 0.0 : _pulseController.value;

          return CustomPaint(
            painter: isActive
                ? _ListeningAuraPainter(
                    pulseProgress: pulseValue,
                    isSpeaking: isSpeaking,
                    accentColor: isSpeaking ? AppColors.guidance : AppColors.primary,
                  )
                : null,
            child: child,
          );
        },
        child: AnimatedContainer(
          duration: AppMotion.getDuration(context, AppMotion.standard),
          curve: AppMotion.expressiveOut,
          height: AppSpacing.primaryActionHeight,
          decoration: BoxDecoration(
            borderRadius: AppSpacing.roundedXl,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: isBusy
                  ? [AppColors.surfaceElevated, AppColors.surfaceElevated]
                  : (isActive
                      ? [const Color(0xFF1E293B), const Color(0xFF0F172A)] // Tactile Obsidian Slate
                      : [AppColors.primary, const Color(0xFF0D9488)]), // Luminous Teal
            ),
            border: Border.all(
              color: isActive ? AppColors.primary.withValues(alpha: 0.6) : AppColors.borderHairline,
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: (isActive ? AppColors.primary : AppColors.primary).withValues(alpha: isActive ? 0.25 : 0.4),
                blurRadius: isActive ? 20 : 28,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: AppSpacing.roundedXl,
              onTap: isBusy ? null : (isActive ? widget.onStop : widget.onStart),
              splashColor: Colors.white.withValues(alpha: 0.15),
              highlightColor: Colors.white.withValues(alpha: 0.08),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Morphing Icon
                    if (isBusy)
                      const SizedBox(
                        width: 28,
                        height: 28,
                        child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white),
                      )
                    else
                      AnimatedSwitcher(
                        duration: AppMotion.getDuration(context, AppMotion.quick),
                        transitionBuilder: (child, anim) => ScaleTransition(scale: anim, child: child),
                        child: Icon(
                          isActive ? Icons.pause_circle_filled_rounded : Icons.play_arrow_rounded,
                          key: ValueKey(isActive),
                          size: 40,
                          color: Colors.white,
                        ),
                      ),
                    const SizedBox(width: AppSpacing.md),

                    // Label with readable typography
                    Flexible(
                      child: Text(
                        isBusy
                            ? (widget.status == AssistanceStatus.starting ? 'STARTING...' : 'PAUSING...')
                            : label,
                        style: AppTypography.labelLarge.copyWith(
                          fontSize: 18,
                          letterSpacing: 1.1,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Concentric gentle listening pulse painter for active feedback.
class _ListeningAuraPainter extends CustomPainter {
  final double pulseProgress;
  final bool isSpeaking;
  final Color accentColor;

  _ListeningAuraPainter({
    required this.pulseProgress,
    required this.isSpeaking,
    required this.accentColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    // Draw two expanding wave rings
    for (int i = 0; i < 2; i++) {
      final wave = (pulseProgress + (i * 0.5)) % 1.0;
      final opacity = (1.0 - wave) * (isSpeaking ? 0.45 : 0.25);

      ringPaint.color = accentColor.withValues(alpha: opacity.clamp(0.0, 1.0));
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(
            center: center,
            width: size.width + (wave * 24.0),
            height: size.height + (wave * 18.0),
          ),
          AppSpacing.radiusXl,
        ),
        ringPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _ListeningAuraPainter oldDelegate) {
    return oldDelegate.pulseProgress != pulseProgress ||
        oldDelegate.isSpeaking != isSpeaking ||
        oldDelegate.accentColor != accentColor;
  }
}
