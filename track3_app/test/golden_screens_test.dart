import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/config/app_config.dart';
import 'package:track3_app/presentation/ui_mode_controller.dart';
import 'package:track3_app/screens/a_eye_mode_screen.dart';
import 'package:track3_app/screens/assistance_screen.dart';
import 'package:track3_app/screens/onboarding_screen.dart';
import 'dart:typed_data';
import 'package:track3_app/camera/camera_service.dart';
import 'package:track3_app/services/haptic_service.dart';
import 'package:track3_app/services/screen_curtain_service.dart';
import 'package:track3_app/services/session_service.dart';
import 'package:track3_app/services/speech_service.dart';
import 'package:track3_app/services/track2_api_service.dart';
import 'package:track3_app/theme/app_theme.dart';

class StubCameraService extends CameraService {
  @override
  bool get isInitialized => true;

  @override
  Future<void> initialize({dynamic resolution}) async {}

  @override
  Future<Uint8List?> captureFrameJpeg({int quality = 75, int maxWidth = 720}) async {
    return Uint8List.fromList([1, 2, 3]);
  }
}

class StubApiService extends Track2ApiService {
  StubApiService({required super.config});

  @override
  Future<BridgeHealthStatus> checkHealth({Duration timeout = const Duration(seconds: 4)}) async {
    return const BridgeHealthStatus(isHealthy: true, vlmMode: 'mock', track2Available: true);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AppConfig config;
  late StubCameraService mockCamera;
  late StubApiService mockApi;
  late SpeechService speechService;
  late HapticService hapticService;
  late SessionService sessionService;
  late UiModeController uiModeController;
  late ScreenCurtainService curtainService;

  setUp(() {
    config = AppConfig(backendBaseUrl: 'http://10.18.185.180:5000');
    mockCamera = StubCameraService();
    mockApi = StubApiService(config: config);
    speechService = SpeechService(config: config);
    hapticService = HapticService(config: config);

    sessionService = SessionService(
      config: config,
      cameraService: mockCamera,
      apiService: mockApi,
      speechService: speechService,
      hapticService: hapticService,
    );

    uiModeController = UiModeController();
    curtainService = ScreenCurtainService();
  });

  Widget createTestApp({
    required Size screenSize,
    double textScale = 1.0,
    bool highContrast = false,
    required Widget child,
  }) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: AppTheme.buildTheme(highContrast: highContrast),
      home: MediaQuery(
        data: MediaQueryData(
          size: screenSize,
          textScaler: TextScaler.linear(textScale),
        ),
        child: SizedBox(
          width: screenSize.width,
          height: screenSize.height,
          child: child,
        ),
      ),
    );
  }

  group('Visual Responsive & Golden Layout Tests', () {
    testWidgets('Assistance Screen renders cleanly at Standard Phone size (375x812)', (tester) async {
      await tester.binding.setSurfaceSize(const Size(375, 812));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(375, 812),
          child: AssistanceScreen(
            config: config,
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('START ASSISTANCE'), findsOneWidget);
      expect(find.text('Ready & Scanning'), findsOneWidget);
      expect(find.text('A-Eye is standing by.'), findsOneWidget);

      await expectLater(
        find.byType(AssistanceScreen),
        matchesGoldenFile('goldens/assistance_screen_standard_375x812.png'),
      );
    });

    testWidgets('Assistance Screen renders cleanly at Tall Modern Phone size (412x915)', (tester) async {
      await tester.binding.setSurfaceSize(const Size(412, 915));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(412, 915),
          child: AssistanceScreen(
            config: config,
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('START ASSISTANCE'), findsOneWidget);
      await expectLater(
        find.byType(AssistanceScreen),
        matchesGoldenFile('goldens/assistance_screen_tall_412x915.png'),
      );
    });

    testWidgets('Assistance Screen renders cleanly at Compact Small Phone size (320x640)', (tester) async {
      await tester.binding.setSurfaceSize(const Size(320, 640));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(320, 640),
          child: AssistanceScreen(
            config: config,
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('START ASSISTANCE'), findsOneWidget);
      expect(tester.takeException(), isNull, reason: 'Small phone must not overflow');

      await expectLater(
        find.byType(AssistanceScreen),
        matchesGoldenFile('goldens/assistance_screen_compact_320x640.png'),
      );
    });

    testWidgets('Assistance Screen renders cleanly at 200% Accessibility Text Scaling', (tester) async {
      await tester.binding.setSurfaceSize(const Size(375, 812));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(375, 812),
          textScale: 2.0, // 200% text scale!
          child: AssistanceScreen(
            config: config,
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('START ASSISTANCE'), findsOneWidget);
      expect(tester.takeException(), isNull, reason: '200% text scaling must not cause overflow');

      await expectLater(
        find.byType(AssistanceScreen),
        matchesGoldenFile('goldens/assistance_screen_200_percent_text.png'),
      );
    });

    testWidgets('Assistance Screen renders in High Contrast Mode', (tester) async {
      await tester.binding.setSurfaceSize(const Size(375, 812));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(375, 812),
          highContrast: true,
          child: AssistanceScreen(
            config: config,
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          ),
        ),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(find.text('START ASSISTANCE'), findsOneWidget);

      await expectLater(
        find.byType(AssistanceScreen),
        matchesGoldenFile('goldens/assistance_screen_high_contrast.png'),
      );
    });

    testWidgets('A-Eye Dark Mode Screen renders pure OLED black with single TalkBack semantic node', (tester) async {
      await tester.binding.setSurfaceSize(const Size(375, 812));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(375, 812),
          child: AEyeModeScreen(
            sessionService: sessionService,
            uiModeController: uiModeController,
            curtainService: curtainService,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(AEyeModeScreen), findsOneWidget);
      expect(find.textContaining('Press & hold 2s to exit dark mode'), findsOneWidget);

      await expectLater(
        find.byType(AEyeModeScreen),
        matchesGoldenFile('goldens/a_eye_mode_screen_dark.png'),
      );
    });

    testWidgets('Onboarding Screen renders voice-first tutorial steps', (tester) async {
      await tester.binding.setSurfaceSize(const Size(375, 812));

      await tester.pumpWidget(
        createTestApp(
          screenSize: const Size(375, 812),
          child: OnboardingScreen(
            uiModeController: uiModeController,
            speechService: speechService,
            onComplete: () {},
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Welcome to A-Eye'), findsOneWidget);
      expect(find.text('CONTINUE'), findsOneWidget);

      await expectLater(
        find.byType(OnboardingScreen),
        matchesGoldenFile('goldens/onboarding_screen_step1.png'),
      );
    });
  });
}
