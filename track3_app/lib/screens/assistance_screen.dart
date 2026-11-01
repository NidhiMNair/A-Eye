import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../presentation/ui_mode_controller.dart';
import '../services/screen_curtain_service.dart';
import '../services/session_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_spacing.dart';
import '../widgets/camera_viewport.dart';
import '../widgets/developer_telemetry_sheet.dart';
import '../widgets/guidance_sheet.dart';
import '../widgets/mode_switch_pill.dart';
import '../widgets/status_capsule.dart';
import '../widgets/tactile_action_button.dart';
import 'a_eye_mode_screen.dart';
import 'settings_screen.dart';

/// The redesigned master home screen for A-Eye Guidance.
/// Implements near full-bleed portrait viewport, floating frosted glass overlays,
/// tactile thumb action control, and seamless A-Eye Dark Mode integration.
class AssistanceScreen extends StatelessWidget {
  final AppConfig config;
  final SessionService sessionService;
  final UiModeController uiModeController;
  final ScreenCurtainService curtainService;

  const AssistanceScreen({
    super.key,
    required this.config,
    required this.sessionService,
    required this.uiModeController,
    required this.curtainService,
  });

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([sessionService, uiModeController]),
      builder: (context, _) {
        final state = sessionService.state;
        final isAEyeMode = uiModeController.isAEyeModeActive;
        final isDevMode = uiModeController.isDeveloperModeEnabled;

        // If A-Eye Mode is active, transition into pure black tactile screen
        if (isAEyeMode) {
          return AEyeModeScreen(
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          );
        }

        return Scaffold(
          backgroundColor: AppColors.background,
          body: SafeArea(
            bottom: true,
            child: Stack(
              fit: StackFit.expand,
              children: [
                // 1. Master Vertical Scrollable Canvas
                SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.md,
                    vertical: AppSpacing.xs,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Top Utility Bar: Mode Switch + Settings & HUD
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Flexible(
                            child: ModeSwitchPill(
                              isAEyeMode: false,
                              onModeChanged: (active) {
                                uiModeController.setAEyeMode(active);
                              },
                            ),
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (isDevMode)
                                IconButton(
                                  icon: const Icon(Icons.analytics_outlined, color: AppColors.primary),
                                  tooltip: 'Open Developer HUD',
                                  onPressed: () {
                                    DeveloperTelemetrySheet.show(
                                      context,
                                      state: state,
                                      backendUrl: config.backendBaseUrl,
                                    );
                                  },
                                ),
                              IconButton(
                                icon: const Icon(Icons.settings_outlined, color: AppColors.textPrimary),
                                tooltip: 'Settings & Configuration',
                                onPressed: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => SettingsScreen(
                                        config: config,
                                        sessionService: sessionService,
                                        uiModeController: uiModeController,
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xs),

                      // Center Floating Status Capsule
                      Center(
                        child: StatusCapsule(state: state),
                      ),
                      const SizedBox(height: AppSpacing.sm),

                      // 2. Camera Viewport (Portrait 3:4 undistorted with spatial overlays)
                      CameraViewport(
                        cameraService: sessionService.cameraService,
                        isAssistanceActive: state.status.isActive,
                        isDeveloperMode: isDevMode,
                        latestResult: state.latestResult,
                      ),
                      const SizedBox(height: AppSpacing.md),

                      // 3. Guidance Card (Punctuation sanitized, Severity badge, Lexend font)
                      GuidanceSheet(
                        state: state,
                        isDeveloperMode: isDevMode,
                        onReplaySpeech: () {
                          final msg = state.lastSpokenMessage;
                          if (msg.isNotEmpty) {
                            sessionService.speechService.speak(msg, interrupt: true);
                          }
                        },
                      ),
                      const SizedBox(height: AppSpacing.md),

                      // 4. Primary Tactile Action Control (Morphing button with listening aura)
                      TactileActionButton(
                        status: state.status,
                        onStart: sessionService.startAssistance,
                        onStop: sessionService.stopAssistance,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
