import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../services/session_service.dart';
import '../widgets/big_action_button.dart';
import '../widgets/camera_preview_widget.dart';
import '../widgets/status_banner.dart';
import '../widgets/transcript_card.dart';
import 'settings_screen.dart';

/// Main voice-first assistive navigation screen.
class AssistanceScreen extends StatelessWidget {
  final AppConfig config;
  final SessionService sessionService;

  const AssistanceScreen({
    super.key,
    required this.config,
    required this.sessionService,
  });

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: sessionService,
      builder: (context, _) {
        final state = sessionService.state;

        return Scaffold(
          appBar: AppBar(
            title: const Text('A-Eye Guidance'),
            centerTitle: true,
            actions: [
              IconButton(
                icon: const Icon(Icons.settings),
                tooltip: 'Settings',
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => SettingsScreen(
                        config: config,
                        sessionService: sessionService,
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // 1. Status Banner
                  StatusBanner(state: state),
                  const SizedBox(height: 12),

                  // 2. Camera Preview (live when active)
                  CameraPreviewWidget(
                    cameraService: sessionService.cameraService,
                    isAssistanceActive: state.status.isActive,
                  ),
                  const SizedBox(height: 16),

                  // 3. Giant Primary Touch Target
                  BigActionButton(
                    status: state.status,
                    onStart: sessionService.startAssistance,
                    onStop: sessionService.stopAssistance,
                  ),
                  const SizedBox(height: 16),

                  // 4. Latest Guidance Transcript & Performance
                  TranscriptCard(
                    state: state,
                    recentEvents: sessionService.recentEvents,
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
