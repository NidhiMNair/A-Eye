import 'package:flutter/material.dart';

import '../presentation/ui_mode_controller.dart';
import '../services/speech_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_motion.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';

/// First-run onboarding experience: voice-led and visual.
/// Clearly communicates core capabilities, mandatory safety boundaries, and privacy.
class OnboardingScreen extends StatefulWidget {
  final UiModeController uiModeController;
  final SpeechService speechService;
  final VoidCallback onComplete;

  const OnboardingScreen({
    super.key,
    required this.uiModeController,
    required this.speechService,
    required this.onComplete,
  });

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<_OnboardingStep> _steps = const [
    _OnboardingStep(
      icon: Icons.visibility_rounded,
      iconColor: AppColors.primary,
      title: 'Welcome to A-Eye',
      description: 'Your voice-first assistive copilot. A-Eye continuously observes your path and describes obstacles, hazards, and navigation cues in real time.',
      voiceSummary: 'Welcome to A-Eye. Your voice-first assistive copilot for real-time obstacle and hazard awareness.',
    ),
    _OnboardingStep(
      icon: Icons.shield_rounded,
      iconColor: AppColors.guidance,
      title: 'Important Safety Notice',
      description: 'Never assume any path is completely safe. A-Eye is an assistive aid designed to supplement—not replace—your cane, guide dog, and sensory judgment.',
      voiceSummary: 'Safety notice: A-Eye is an assistive tool. Never assume a path is completely safe. Always use your cane or primary mobility aid.',
    ),
    _OnboardingStep(
      icon: Icons.dark_mode_rounded,
      iconColor: AppColors.secondary,
      title: 'A-Eye Dark Mode',
      description: 'For discreet, battery-saving navigation, switch to A-Eye Mode. The screen goes completely dark while audio guidance and haptics continue uninterrupted.',
      voiceSummary: 'A-Eye dark mode allows you to navigate with the screen completely black to save battery and avoid light glare.',
    ),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _speakCurrentStep(0);
    });
  }

  void _speakCurrentStep(int index) {
    if (index >= 0 && index < _steps.length) {
      widget.speechService.speak(_steps[index].voiceSummary, interrupt: true);
    }
  }

  void _onFinish() {
    widget.uiModeController.setOnboardingCompleted(true);
    widget.onComplete();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isLastPage = _currentPage == _steps.length - 1;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl, vertical: AppSpacing.lg),
          child: Column(
            children: [
              // Top Bar: Skip button
              Align(
                alignment: Alignment.topRight,
                child: TextButton(
                  onPressed: _onFinish,
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.textSecondary,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                  child: const Text('Skip', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                ),
              ),

              // Page Carousel
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  itemCount: _steps.length,
                  onPageChanged: (idx) {
                    setState(() => _currentPage = idx);
                    _speakCurrentStep(idx);
                  },
                  itemBuilder: (context, idx) {
                    final step = _steps[idx];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 100,
                            height: 100,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: step.iconColor.withValues(alpha: 0.15),
                              border: Border.all(color: step.iconColor.withValues(alpha: 0.4), width: 2),
                            ),
                            child: Icon(step.icon, size: 48, color: step.iconColor),
                          ),
                          const SizedBox(height: AppSpacing.xxl),

                          Text(
                            step.title,
                            textAlign: TextAlign.center,
                            style: AppTypography.displayMedium.copyWith(fontSize: 24),
                          ),
                          const SizedBox(height: AppSpacing.md),

                          Text(
                            step.description,
                            textAlign: TextAlign.center,
                            style: AppTypography.bodyLarge.copyWith(
                              color: AppColors.textSecondary,
                              height: 1.5,
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),

              // Dots indicator
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(_steps.length, (idx) {
                  final isSelected = idx == _currentPage;
                  return AnimatedContainer(
                    duration: AppMotion.standard,
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: isSelected ? 24 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(4),
                      color: isSelected ? AppColors.primary : AppColors.textMuted.withValues(alpha: 0.3),
                    ),
                  );
                }),
              ),
              const SizedBox(height: AppSpacing.xxl),

              // Bottom Navigation Primary Action
              SizedBox(
                width: double.infinity,
                height: 58,
                child: FilledButton(
                  onPressed: isLastPage
                      ? _onFinish
                      : () {
                          _pageController.nextPage(
                            duration: AppMotion.standard,
                            curve: AppMotion.expressiveOut,
                          );
                        },
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(borderRadius: AppSpacing.roundedLg),
                  ),
                  child: Text(
                    isLastPage ? 'GET STARTED' : 'CONTINUE',
                    style: AppTypography.labelLarge.copyWith(
                      color: Colors.white,
                      letterSpacing: 1.2,
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

class _OnboardingStep {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String description;
  final String voiceSummary;

  const _OnboardingStep({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.description,
    required this.voiceSummary,
  });
}
