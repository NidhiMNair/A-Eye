import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/config/app_config.dart';
import 'package:track3_app/models/models.dart';
import 'package:track3_app/output/assistance_output_policy.dart';
import 'package:track3_app/services/haptic_service.dart';
import 'package:track3_app/services/speech_service.dart';

class MockSpeechService extends SpeechService {
  MockSpeechService({required super.config});

  final List<String> spokenMessages = [];
  final List<bool> interruptFlags = [];
  bool _mockSpeaking = false;

  @override
  bool get isSpeaking => _mockSpeaking;

  void setSpeaking(bool speaking) {
    _mockSpeaking = speaking;
  }

  @override
  Future<void> speak(String text, {bool interrupt = false}) async {
    spokenMessages.add(text);
    interruptFlags.add(interrupt);
    _mockSpeaking = true;
  }

  @override
  Future<void> stop() async {
    _mockSpeaking = false;
  }
}

class MockHapticService extends HapticService {
  MockHapticService({required super.config});

  int alertCount = 0;
  int guidanceCount = 0;
  int infoCount = 0;

  @override
  Future<void> vibrateAlert() async {
    alertCount++;
  }

  @override
  Future<void> vibrateGuidance() async {
    guidanceCount++;
  }

  @override
  Future<void> vibrateInfo() async {
    infoCount++;
  }
}

Track2Result createTestResult({
  required AssistanceCategory category,
  required PriorityLevel priority,
  required String message,
  List<String> hazards = const [],
}) {
  return Track2Result(
    frameId: 'test_f1',
    timestampMs: 1000,
    decision: AssistanceDecision(
      category: category,
      priority: priority,
      message: message,
      relevantItems: [
        PrioritizedItem(
          item: 'test_obj',
          priority: priority,
          reason: 'test reason',
          isHazard: category == AssistanceCategory.alert,
        ),
      ],
    ),
    perception: PerceptionResult(
      frameId: 'test_f1',
      timestampMs: 1000,
      source: 'mock',
      objects: [],
      sceneLabel: 'test',
      hazards: hazards,
      uncertainties: [],
    ),
    spatial: const SpatialAnalysis(
      frameId: 'test_f1',
      objects: [],
      centralObjects: [],
      prominentObjects: [],
      sceneLabel: 'test',
    ),
    context: const ContextAnalysis(),
    summary: 'summary',
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late AppConfig config;
  late MockSpeechService mockSpeech;
  late MockHapticService mockHaptics;
  late AssistanceOutputPolicy policy;

  setUp(() {
    config = AppConfig(
      alertCooldownMs: 1000,
      guidanceCooldownMs: 2000,
      infoCooldownMs: 3000,
    );
    mockSpeech = MockSpeechService(config: config);
    mockHaptics = MockHapticService(config: config);
    policy = AssistanceOutputPolicy(
      speechService: mockSpeech,
      hapticService: mockHaptics,
      config: config,
    );
  });

  group('4, 5, 6, 7: Output Policy, Speech Deduplication & Interrupts', () {
    test('4: Duplicate guidance results are deduplicated and suppressed', () async {
      final res1 = createTestResult(
        category: AssistanceCategory.guidance,
        priority: PriorityLevel.medium,
        message: 'Door detected on the left',
      );

      // First presentation should speak
      await policy.processResult(res1);
      expect(mockSpeech.spokenMessages.length, 1);
      expect(mockSpeech.spokenMessages.first, contains('Door detected on the left'));

      // Immediate identical second presentation should be suppressed
      await policy.processResult(res1);
      expect(mockSpeech.spokenMessages.length, 1, reason: 'Duplicate should be suppressed');
    });

    test('5: Message speaks again after cooldown expires', () async {
      final res1 = createTestResult(
        category: AssistanceCategory.alert,
        priority: PriorityLevel.high,
        message: 'Chair directly ahead',
      );

      await policy.processResult(res1);
      expect(mockSpeech.spokenMessages.length, 1);

      // Wait for alert cooldown (1000ms configured in test)
      await Future<void>.delayed(const Duration(milliseconds: 1050));

      await policy.processResult(res1);
      expect(mockSpeech.spokenMessages.length, 2, reason: 'Should speak after cooldown expires');
    });

    test('6: Urgent HIGH alert interrupts lower-priority speech immediately', () async {
      final guidanceRes = createTestResult(
        category: AssistanceCategory.guidance,
        priority: PriorityLevel.medium,
        message: 'Path turns slightly right',
      );
      final alertRes = createTestResult(
        category: AssistanceCategory.alert,
        priority: PriorityLevel.high,
        message: 'Obstacle detected in central path',
        hazards: ['central obstacle'],
      );

      // Start guidance speech
      await policy.processResult(guidanceRes);
      expect(mockSpeech.spokenMessages.length, 1);
      expect(mockSpeech.interruptFlags.first, isFalse);

      // High alert arrives while guidance is speaking
      mockSpeech.setSpeaking(true);
      await policy.processResult(alertRes);

      expect(mockSpeech.spokenMessages.length, 2);
      expect(mockSpeech.interruptFlags.last, isTrue, reason: 'Urgent alert must interrupt active speech');
    });

    test('7: Haptic feedback triggers appropriate vibration for priority levels', () async {
      final alertRes = createTestResult(
        category: AssistanceCategory.alert,
        priority: PriorityLevel.high,
        message: 'Hazard ahead',
      );
      final guidanceRes = createTestResult(
        category: AssistanceCategory.guidance,
        priority: PriorityLevel.medium,
        message: 'Door on right',
      );

      await policy.processResult(alertRes);
      expect(mockHaptics.alertCount, 1);

      policy.reset();
      await policy.processResult(guidanceRes);
      expect(mockHaptics.guidanceCount, 1);
    });
  });
}
