import 'package:flutter/material.dart';

import 'app.dart';
import 'camera/camera_service.dart';
import 'config/app_config.dart';
import 'services/haptic_service.dart';
import 'services/session_service.dart';
import 'services/speech_service.dart';
import 'services/track2_api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final config = AppConfig();
  final cameraService = CameraService();
  final apiService = Track2ApiService(config: config);
  final speechService = SpeechService(config: config);
  final hapticService = HapticService(config: config);

  final sessionService = SessionService(
    config: config,
    cameraService: cameraService,
    apiService: apiService,
    speechService: speechService,
    hapticService: hapticService,
  );

  runApp(AEyeApp(
    config: config,
    sessionService: sessionService,
  ));
}
