import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/camera/camera_service.dart';
import 'package:track3_app/config/app_config.dart';
import 'package:track3_app/models/models.dart';
import 'package:track3_app/services/frame_scheduler.dart';
import 'package:track3_app/services/track2_api_service.dart';

class MockCameraService extends CameraService {
  int captureCount = 0;
  Uint8List? mockFrameBytes = Uint8List.fromList([1, 2, 3, 4]);

  @override
  bool get isInitialized => true;

  @override
  Future<Uint8List?> captureFrameJpeg({int quality = 75, int maxWidth = 720}) async {
    captureCount++;
    return mockFrameBytes;
  }
}

class MockTrack2ApiService extends Track2ApiService {
  MockTrack2ApiService({required super.config});

  final List<String> submittedFrameIds = [];
  Completer<Track2Result>? inFlightCompleter;

  @override
  Future<Track2Result> processFrames({
    required List<Uint8List> frameBytesList,
    String? frameId,
    int? timestampMs,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    submittedFrameIds.add(frameId ?? 'unknown');

    if (inFlightCompleter != null) {
      return await inFlightCompleter!.future;
    }

    return Track2Result(
      frameId: frameId ?? 'f1',
      timestampMs: timestampMs ?? 0,
      decision: const AssistanceDecision(
        category: AssistanceCategory.info,
        priority: PriorityLevel.low,
        message: 'Mock response',
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

void main() {
  group('8, 9: Frame Scheduler & Duplicate Prevention', () {
    test('8: Frame scheduler skips and drops frame when inference is in flight', () async {
      final config = AppConfig(samplingIntervalMs: 50);
      final camera = MockCameraService();
      final api = MockTrack2ApiService(config: config);

      final scheduler = FrameScheduler(
        cameraService: camera,
        apiService: api,
        config: config,
      );

      // Simulate a long-running inference request that does not complete immediately
      final completer = Completer<Track2Result>();
      api.inFlightCompleter = completer;

      scheduler.start();

      // Allow 4 tick intervals to elapse while inference is blocked
      await Future<void>.delayed(const Duration(milliseconds: 230));

      final stats = scheduler.currentStats;
      expect(stats.isCurrentlyInferring, isTrue);
      expect(api.submittedFrameIds.length, 1, reason: 'Only 1 request should be submitted');
      expect(stats.droppedFrames, greaterThanOrEqualTo(2), reason: 'Stale frames must be discarded');

      // Complete the inference
      completer.complete(
        Track2Result(
          frameId: 'done',
          timestampMs: 0,
          decision: const AssistanceDecision(
            category: AssistanceCategory.none,
            priority: PriorityLevel.low,
            message: 'done',
            relevantItems: [],
          ),
          perception: const PerceptionResult(
            frameId: 'done',
            timestampMs: 0,
            source: 'mock',
            objects: [],
            sceneLabel: 'test',
            hazards: [],
            uncertainties: [],
          ),
          spatial: const SpatialAnalysis(
            frameId: 'done',
            objects: [],
            centralObjects: [],
            prominentObjects: [],
            sceneLabel: 'test',
          ),
          context: const ContextAnalysis(),
          summary: 'done',
        ),
      );

      scheduler.stop();
      scheduler.dispose();
    });

    test('9: Consecutive captured frames generate unique frame IDs', () async {
      final config = AppConfig(samplingIntervalMs: 50);
      final camera = MockCameraService();
      final api = MockTrack2ApiService(config: config);

      final scheduler = FrameScheduler(
        cameraService: camera,
        apiService: api,
        config: config,
      );

      scheduler.start();

      // Wait for at least 2 ticks
      await Future<void>.delayed(const Duration(milliseconds: 140));

      scheduler.stop();
      scheduler.dispose();

      expect(api.submittedFrameIds.length, greaterThanOrEqualTo(2));
      final ids = api.submittedFrameIds.toSet();
      expect(ids.length, equals(api.submittedFrameIds.length), reason: 'Every frame ID must be unique');
    });
  });
}
