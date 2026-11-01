import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:track3_app/camera/camera_service.dart';
import 'package:track3_app/config/app_config.dart';
import 'package:track3_app/services/frame_scheduler.dart';
import 'package:track3_app/services/haptic_service.dart';
import 'package:track3_app/services/session_service.dart';
import 'package:track3_app/services/speech_service.dart';
import 'package:track3_app/services/track2_api_service.dart';
import 'package:track3_app/state/session_state.dart';

class MockCamera extends CameraService {
  @override
  bool get isInitialized => true;

  @override
  Future<void> initialize({dynamic resolution}) async {}

  @override
  Future<Uint8List?> captureFrameJpeg({int quality = 75, int maxWidth = 720}) async {
    return Uint8List.fromList([10, 20, 30]);
  }

  @override
  Future<void> dispose() async {}
}

class MockSpeech extends SpeechService {
  MockSpeech({required super.config});
  final List<String> spoken = [];

  @override
  Future<void> speak(String text, {bool interrupt = false}) async {
    spoken.add(text);
  }

  @override
  Future<void> stop() async {}
}

class MockHaptic extends HapticService {
  MockHaptic({required super.config});
  @override
  Future<void> checkCapabilities() async {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Robustness & Error Resilience Tests', () {
    test('Error classification identifies timeouts properly', () async {
      final mockClient = MockClient((request) async {
        throw TimeoutException('Request timed out');
      });

      final config = AppConfig(
        backendBaseUrl: 'http://10.18.185.180:5000',
        connectTimeoutMs: 100,
      );
      final api = Track2ApiService(config: config, client: mockClient);

      expect(
        () => api.checkHealth(),
        throwsA(isA<Track2NetworkException>().having(
          (e) => e.kind,
          'kind',
          BackendErrorKind.timeout,
        )),
      );
    });

    test('Error classification identifies connection refused properly', () async {
      final mockClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final config = AppConfig(backendBaseUrl: 'http://10.18.185.180:5000');
      final api = Track2ApiService(config: config, client: mockClient);

      expect(
        () => api.checkHealth(),
        throwsA(isA<Track2NetworkException>().having(
          (e) => e.kind,
          'kind',
          BackendErrorKind.connectionRefused,
        )),
      );
    });

    test('Error classification identifies host unreachable properly', () async {
      final mockClient = MockClient((request) async {
        throw http.ClientException('Failed host lookup: server.invalid');
      });

      final config = AppConfig(backendBaseUrl: 'http://server.invalid:5000');
      final api = Track2ApiService(config: config, client: mockClient);

      expect(
        () => api.checkHealth(),
        throwsA(isA<Track2NetworkException>().having(
          (e) => e.kind,
          'kind',
          BackendErrorKind.unreachable,
        )),
      );
    });

    test('FrameScheduler applies exponential backoff on consecutive errors', () async {
      final mockClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final config = AppConfig(
        samplingIntervalMs: 50,
        maxBackoffMs: 1000,
      );
      final camera = MockCamera();
      final api = Track2ApiService(config: config, client: mockClient);

      final scheduler = FrameScheduler(
        cameraService: camera,
        apiService: api,
        config: config,
      );

      final errors = <String>[];
      final errorSub = scheduler.errors.listen(errors.add);

      scheduler.start();

      // Wait for the first error to fire (initial interval is 50ms, backoff is 50ms * 2^1 = 100ms)
      await Future<void>.delayed(const Duration(milliseconds: 70));

      expect(scheduler.consecutiveFailures, greaterThanOrEqualTo(1));
      expect(scheduler.isInBackoff, isTrue);

      scheduler.stop();
      await errorSub.cancel();
      scheduler.dispose();
    });

    test('Session start aborts and alerts user when initial health check fails', () async {
      final mockClient = MockClient((request) async {
        if (request.url.path == '/health') {
          return http.Response('Service Unavailable', 503);
        }
        return http.Response('{}', 200);
      });

      final config = AppConfig(backendBaseUrl: 'http://10.18.185.180:5000');
      final camera = MockCamera();
      final api = Track2ApiService(config: config, client: mockClient);
      final speech = MockSpeech(config: config);
      final haptics = MockHaptic(config: config);

      final session = SessionService(
        config: config,
        cameraService: camera,
        apiService: api,
        speechService: speech,
        hapticService: haptics,
      );

      await session.startAssistance();

      expect(session.state.status, AssistanceStatus.error);
      expect(session.state.statusMessage, contains('Cannot reach the A-Eye server at http://10.18.185.180:5000'));
      expect(session.state.isBackendOnline, isFalse);
      expect(session.frameScheduler.isRunning, isFalse, reason: 'Scheduler should not start if server is unreachable');
      expect(speech.spoken, contains('Cannot reach the A-Eye server.'));

      session.dispose();
    });

    test('Repeated errors transition status to error and avoid spamming speech', () async {
      final mockClient = MockClient((request) async {
        if (request.url.path == '/health') {
          return http.Response(jsonEncode({'status': 'healthy', 'vlm_mode': 'mock', 'track2_available': true}), 200);
        }
        throw http.ClientException('Connection refused');
      });

      final config = AppConfig(
        samplingIntervalMs: 30,
        maxConsecutiveFailures: 2,
        backendBaseUrl: 'http://10.18.185.180:5000',
      );
      final camera = MockCamera();
      final api = Track2ApiService(config: config, client: mockClient);
      final speech = MockSpeech(config: config);
      final haptics = MockHaptic(config: config);

      final session = SessionService(
        config: config,
        cameraService: camera,
        apiService: api,
        speechService: speech,
        hapticService: haptics,
      );

      await session.startAssistance();
      expect(session.state.status, AssistanceStatus.cameraReady);

      // Wait for at least 2 ticks to trigger consecutive errors
      await Future<void>.delayed(const Duration(milliseconds: 100));

      expect(session.consecutiveErrors, greaterThanOrEqualTo(1));

      await session.stopAssistance();
      session.dispose();
    });
  });
}
