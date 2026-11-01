import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../presentation/ui_mode_controller.dart';
import '../services/screen_curtain_service.dart';
import '../services/session_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_motion.dart';
import '../theme/app_typography.dart';

/// A-Eye Mode Screen: Pure OLED black tactile instrument surface.
/// Minimizes light emission, manages hardware brightness dimming,
/// wake lock, immersive sticky system bars, and accidental touch rejection.
class AEyeModeScreen extends StatefulWidget {
  final SessionService sessionService;
  final UiModeController uiModeController;
  final ScreenCurtainService curtainService;

  const AEyeModeScreen({
    super.key,
    required this.sessionService,
    required this.uiModeController,
    required this.curtainService,
  });

  @override
  State<AEyeModeScreen> createState() => _AEyeModeScreenState();
}

class _AEyeModeScreenState extends State<AEyeModeScreen> with SingleTickerProviderStateMixin {
  late final AnimationController _holdController;
  bool _isExiting = false;

  @override
  void initState() {
    super.initState();
    _holdController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );

    _holdController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _exitAEyeMode();
      }
    });

    // Activate hardware curtain (dim brightness, wake-lock, immersive mode)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _activateCurtain();
    });
  }

  Future<void> _activateCurtain() async {
    await widget.curtainService.enable();
    widget.sessionService.hapticService.vibrateAlert();
    widget.sessionService.speechService.speak('A-Eye dark mode active. Double tap for guidance, press and hold to exit.');
  }

  Future<void> _exitAEyeMode() async {
    if (_isExiting) return;
    _isExiting = true;

    HapticFeedback.heavyImpact();
    await widget.curtainService.disable();
    widget.sessionService.speechService.speak('Visual screen restored.');
    widget.uiModeController.setAEyeMode(false);
  }

  @override
  void dispose() {
    _holdController.dispose();
    widget.curtainService.disable();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surfaceOled, // True #000000 for zero OLED emission
      body: Semantics(
        label: 'A-Eye Mode is active. Screen is dark to minimize light emission and conserve battery. '
            'Double tap to repeat the latest guidance. Press and hold anywhere for two seconds to exit.',
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onDoubleTap: () {
            // Repeat last guidance
            HapticFeedback.selectionClick();
            final lastSpoken = widget.sessionService.state.lastSpokenMessage;
            if (lastSpoken.isNotEmpty) {
              widget.sessionService.speechService.speak(lastSpoken);
            } else {
              widget.sessionService.speechService.speak('A-Eye is scanning. No obstacles in immediate path.');
            }
          },
          onLongPressStart: (_) {
            HapticFeedback.mediumImpact();
            _holdController.forward();
          },
          onLongPressEnd: (_) {
            if (_holdController.isAnimating) {
              _holdController.reverse();
            }
          },
          child: Stack(
            fit: StackFit.expand,
            children: [
              // Pitch Black Canvas
              Container(color: Colors.black),

              // Animated Hold-to-Exit indicator (discreet, ultra-low luminosity)
              AnimatedBuilder(
                animation: _holdController,
                builder: (context, child) {
                  if (_holdController.value <= 0.01) return const SizedBox.shrink();

                  return Center(
                    child: Container(
                      width: 140,
                      height: 140,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: AppColors.primary.withValues(alpha: 0.3 * _holdController.value),
                          width: 4,
                        ),
                      ),
                      child: CircularProgressIndicator(
                        value: _holdController.value,
                        strokeWidth: 4,
                        color: AppColors.primary.withValues(alpha: 0.6),
                      ),
                    ),
                  );
                },
              ),

              // Bottom discreet hint for sighted assistance (faint 20% opacity)
              Positioned(
                bottom: 32,
                left: 20,
                right: 20,
                child: Center(
                  child: AnimatedOpacity(
                    opacity: 0.25,
                    duration: AppMotion.standard,
                    child: Text(
                      'Press & hold 2s to exit dark mode',
                      style: AppTypography.bodySmall.copyWith(
                        color: Colors.white,
                        letterSpacing: 0.8,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
