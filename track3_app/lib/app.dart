import 'package:flutter/material.dart';

import 'config/app_config.dart';
import 'screens/assistance_screen.dart';
import 'services/session_service.dart';

/// Root application widget for A-Eye Track 3.
class AEyeApp extends StatelessWidget {
  final AppConfig config;
  final SessionService sessionService;

  const AEyeApp({
    super.key,
    required this.config,
    required this.sessionService,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'A-Eye',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.teal,
          brightness: Brightness.dark,
        ),
      ),
      home: AssistanceScreen(
        config: config,
        sessionService: sessionService,
      ),
    );
  }
}
