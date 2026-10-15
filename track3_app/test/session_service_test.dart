import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/camera/camera_service.dart';
import 'package:track3_app/config/app_config.dart';
import 'package:track3_app/models/models.dart';
import 'package:track3_app/services/haptic_service.dart';
import 'package:track3_app/services/session_service.dart';
import 'package:track3_app/services/speech_service.dart';
import 'package:track3_app/services/track2_api_service.dart';
import 'package:track3_app/state/session_state.dart';

class StubCameraService extends CameraService {
  bool initialized = false;
  bool disposed = false;

  @override
  bool get isInitialized => initialized;

  @override
  Future<void> initialize({dynamic resolution}) async {
    initialized = true;
    disposed = false;
  }

  @override
  Future<Uint8List?> captureFrameJpeg({int quality = 75, int maxWidth = 720}) async {
    return Uint8List.fromList([1, 2, 3]);
  }

  @override
  Future<void> dispose() async {
    initialized = false;
    disposed = true;
  }
}

class StubApiService extends Track2ApiService {
  StubApiService({required super.config});

  bool resetSessionCalled = false;

  @override
  Future<BridgeHealthStatus> checkHealth({Duration timeout = const Duration(seconds: 4)}) async {
    return const BridgeHealthStatus(isHealthy: true, vlmMode: 'mock', track2Available: true);
  }

  @override
  Future<void> resetSession({Duration timeout = const Duration(seconds: 5)}) async {
    resetSessionCalled = true;
  }

  @override
  Future<Track2Result> processFrames({
    required List<Uint8List> frameBytesList,
    String? frameId,
    int? timestampMs,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    return Track2Result(
      frameId: frameId ?? 'f1',
      timestampMs: timestampMs ?? 0,
      decision: const AssistanceDecision(
        category: AssistanceCategory.none,
        priority: PriorityLevel.low,
        message: 'None',
        relevantItems: [],
      ),
      perception: PerceptionResult(
        frameId: frameId ?? 'f1',
        timestampMs: timestampMs ?? 0,
        source: 'mock',
        objects: [],
        sceneLabel: 'test',
        hazards: [],
        uncertainties: [],
      ),
      spatial: const SpatialAnalysis(
        frameId: 'f1',
        objects: [],
        centralObjects: [],
        prominentObjects: [],
        sceneLabel: 'test',
      ),
      context: const ContextAnalysis(),
      summary: 'summary',
    );
  }
}

class StubSpeechService extends SpeechService {
  StubSpeechService({required super.config});

  final List<String> spoken = [];

  @override
  Future<void> speak(String text, {bool interrupt = false}) async {
    spoken.add(text);
  }

  @override
  Future<void> stop() async {}
}

class StubHapticService extends HapticService {
  StubHapticService({required super.config});
  @override
  Future<void> checkCapabilities() async {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  group('11: Session Lifecycle State Transitions', () {
    test('Starts at idle, transitions to cameraReady/active on start, and returns to idle on stop', () async {
      final config = AppConfig(samplingIntervalMs: 500);
      final camera = StubCameraService();
      final api = StubApiService(config: config);
      final speech = StubSpeechService(config: config);
      final haptics = StubHapticService(config: config);

      final session = SessionService(
        config: config,
        cameraService: camera,
        apiService: api,
        speechService: speech,
        hapticService: haptics,
      );

      expect(session.state.status, AssistanceStatus.idle);

      // Start assistance
      await session.startAssistance();

      expect(session.state.status, AssistanceStatus.cameraReady);
      expect(camera.initialized, isTrue);
      expect(api.resetSessionCalled, isTrue, reason: 'Must reset remote Track 2 context on start');
      expect(session.frameScheduler.isRunning, isTrue);
      expect(speech.spoken, contains('A-Eye assistance started.'));

      // Stop assistance
      await session.stopAssistance();

      expect(session.state.status, AssistanceStatus.idle);
      expect(camera.disposed, isTrue);
      expect(session.frameScheduler.isRunning, isFalse);
      expect(speech.spoken, contains('Assistance stopped.'));

      session.dispose();
    });
  });
}
