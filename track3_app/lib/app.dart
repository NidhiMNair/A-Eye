import 'package:flutter/material.dart';

import 'config/app_config.dart';
import 'presentation/ui_mode_controller.dart';
import 'screens/assistance_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/screen_curtain_service.dart';
import 'services/session_service.dart';
import 'theme/app_theme.dart';

/// Root application widget for A-Eye Track 3.
class AEyeApp extends StatefulWidget {
  final AppConfig config;
  final SessionService sessionService;
  final UiModeController? uiModeController;
  final ScreenCurtainService? curtainService;

  const AEyeApp({
    super.key,
    required this.config,
    required this.sessionService,
    this.uiModeController,
    this.curtainService,
  });

  @override
  State<AEyeApp> createState() => _AEyeAppState();
}

class _AEyeAppState extends State<AEyeApp> {
  late final UiModeController _uiModeController;
  late final ScreenCurtainService _curtainService;

  @override
  void initState() {
    super.initState();
    _uiModeController = widget.uiModeController ?? UiModeController();
    _curtainService = widget.curtainService ?? ScreenCurtainService();

    if (widget.uiModeController == null) {
      _uiModeController.initialize();
    }
  }

  @override
  void dispose() {
    if (widget.curtainService == null) {
      _curtainService.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _uiModeController,
      builder: (context, _) {
        final highContrast = _uiModeController.isHighContrastEnabled;

        return MaterialApp(
          title: 'A-Eye Guidance',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.buildTheme(highContrast: highContrast),
          home: !_uiModeController.hasCompletedOnboarding
              ? OnboardingScreen(
                  uiModeController: _uiModeController,
                  speechService: widget.sessionService.speechService,
                  onComplete: () {
                    setState(() {});
                  },
                )
              : AssistanceScreen(
                  config: widget.config,
                  sessionService: widget.sessionService,
                  uiModeController: _uiModeController,
                  curtainService: _curtainService,
                ),
        );
      },
    );
  }
}
