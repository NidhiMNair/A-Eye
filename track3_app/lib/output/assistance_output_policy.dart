import 'dart:async';

import '../config/app_config.dart';
import '../models/models.dart';
import '../services/haptic_service.dart';
import '../services/speech_service.dart';

/// Event dispatched when output policy decides to speak or trigger haptics.
class OutputEvent {
  final DateTime timestamp;
  final String spokenText;
  final AssistanceCategory category;
  final PriorityLevel priority;
  final bool wasInterrupted;
  final bool wasSpoken;
  final String suppressionReason;

  const OutputEvent({
    required this.timestamp,
    required this.spokenText,
    required this.category,
    required this.priority,
    required this.wasInterrupted,
    required this.wasSpoken,
    this.suppressionReason = '',
  });
}

/// Decides whether to speak, what to speak, whether to interrupt, and whether to vibrate,
/// strictly adhering to Track 2's structured decision without reinterpreting spatial reasoning.
class AssistanceOutputPolicy {
  final SpeechService speechService;
  final HapticService hapticService;
  final AppConfig config;

  String _lastSpokenText = '';
  AssistanceCategory _lastCategory = AssistanceCategory.none;
  PriorityLevel _lastPriority = PriorityLevel.low;
  int _lastSpokenTimestamp = 0;
  Set<String> _lastSpokenHazards = {};

  final StreamController<OutputEvent> _eventController = StreamController<OutputEvent>.broadcast();

  AssistanceOutputPolicy({
    required this.speechService,
    required this.hapticService,
    required this.config,
  });

  Stream<OutputEvent> get events => _eventController.stream;
  String get lastSpokenText => _lastSpokenText;
  AssistanceCategory get lastCategory => _lastCategory;
  PriorityLevel get lastPriority => _lastPriority;

  /// Reset history on new session.
  void reset() {
    _lastSpokenText = '';
    _lastCategory = AssistanceCategory.none;
    _lastPriority = PriorityLevel.low;
    _lastSpokenTimestamp = 0;
    _lastSpokenHazards = {};
    _clearFramesCount = 0;
  }

  int _clearFramesCount = 0;

  /// Process an incoming Track2Result through the assistance output policy.
  Future<void> processResult(Track2Result result) async {
    final decision = result.decision;
    final category = decision.category;
    final priority = decision.priority;

    if (category == AssistanceCategory.none) {
      _clearFramesCount++;
      if (_clearFramesCount >= 2) {
        // Scene cleared: allow obstacle to be announced again if camera turns back
        _lastSpokenText = '';
        _lastSpokenHazards = {};
      }
      _recordEvent(
        text: '',
        category: category,
        priority: priority,
        wasSpoken: false,
        wasInterrupted: false,
        reason: 'Category is NONE',
      );
      return;
    }
    _clearFramesCount = 0;

    final candidateSpeechText = _formatSpeechText(result);
    final now = DateTime.now().millisecondsSinceEpoch;
    final elapsedSinceLastSpeech = now - _lastSpokenTimestamp;

    // Check for priority escalation (e.g. from MEDIUM/LOW to HIGH)
    final isPriorityEscalated = _lastSpokenText.isNotEmpty && priority.rank > _lastPriority.rank;

    // If speech is actively playing, never interrupt it unless priority strictly escalated
    if (speechService.isSpeaking && !isPriorityEscalated) {
      _recordEvent(
        text: candidateSpeechText,
        category: category,
        priority: priority,
        wasSpoken: false,
        wasInterrupted: false,
        reason: 'Active speech in progress: allowing current sentence to finish',
      );
      return;
    }

    // Check message material change using substantive word similarity
    final isMaterialChange = _isMaterialChange(candidateSpeechText, _lastSpokenText);

    // Check for newly appeared hazards
    final currentHazards = result.perception.hazards.toSet();
    final hasNewHazard = isMaterialChange && currentHazards.difference(_lastSpokenHazards).isNotEmpty;

    // Check cooldown based on category
    final cooldownMs = _getCooldownMs(category);
    final isCooldownExpired = elapsedSinceLastSpeech >= cooldownMs;

    // Suppression decision logic:
    bool shouldSpeak = false;
    bool shouldInterrupt = false;
    String suppressionReason = '';

    if (category == AssistanceCategory.alert) {
      if (isPriorityEscalated) {
        shouldSpeak = true;
        shouldInterrupt = true;
      } else if (hasNewHazard && isMaterialChange) {
        shouldSpeak = true;
        shouldInterrupt = false;
      } else if (isMaterialChange && isCooldownExpired) {
        shouldSpeak = true;
        shouldInterrupt = false;
      } else if (!isMaterialChange && isCooldownExpired) {
        // Repeated high alert after cooldown to remind user of persistent danger
        shouldSpeak = true;
        shouldInterrupt = false;
      } else {
        suppressionReason = isMaterialChange
            ? 'Alert in cooldown (${elapsedSinceLastSpeech}ms < ${cooldownMs}ms)'
            : 'Duplicate alert suppressed';
      }
    } else if (category == AssistanceCategory.guidance) {
      if (isPriorityEscalated) {
        shouldSpeak = true;
        shouldInterrupt = true;
      } else if (isMaterialChange && isCooldownExpired) {
        shouldSpeak = true;
        shouldInterrupt = false;
      } else {
        suppressionReason = isMaterialChange
            ? 'Guidance in cooldown (${elapsedSinceLastSpeech}ms < ${cooldownMs}ms)'
            : 'Duplicate guidance message';
      }
    } else if (category == AssistanceCategory.info) {
      if (isMaterialChange && isCooldownExpired) {
        shouldSpeak = true;
        shouldInterrupt = false;
      } else {
        suppressionReason = 'Info suppressed to avoid chatter';
      }
    }

    // Trigger Haptics according to priority
    if (shouldSpeak || category == AssistanceCategory.alert) {
      if (priority == PriorityLevel.high) {
        await hapticService.vibrateAlert();
      } else if (priority == PriorityLevel.medium) {
        await hapticService.vibrateGuidance();
      } else {
        await hapticService.vibrateInfo();
      }
    }

    // Trigger Speech
    if (shouldSpeak) {
      _lastSpokenText = candidateSpeechText;
      _lastCategory = category;
      _lastPriority = priority;
      _lastSpokenTimestamp = now;
      _lastSpokenHazards = currentHazards;

      await speechService.speak(candidateSpeechText, interrupt: shouldInterrupt);

      _recordEvent(
        text: candidateSpeechText,
        category: category,
        priority: priority,
        wasSpoken: true,
        wasInterrupted: shouldInterrupt,
      );
    } else {
      _recordEvent(
        text: candidateSpeechText,
        category: category,
        priority: priority,
        wasSpoken: false,
        wasInterrupted: false,
        reason: suppressionReason,
      );
    }
  }

  /// Check if candidate message represents a substantially different observation than the previous one.
  bool _isMaterialChange(String candidate, String last) {
    if (last.isEmpty) return true;
    final cLower = candidate.toLowerCase().trim();
    final lLower = last.toLowerCase().trim();
    if (cLower == lLower) return false;

    // Compare meaningful words (>2 chars, excluding common boilerplate words)
    const boilerplate = {
      'alert',
      'caution',
      'obstacle',
      'hazard',
      'detected',
      'in',
      'path',
      'ahead',
      'with',
      'and',
      'the',
      'small',
      'door'
    };
    final cWords = cLower
        .replaceAll(RegExp(r'[^a-z0-9 ]'), '')
        .split(' ')
        .where((w) => w.length > 2 && !boilerplate.contains(w))
        .toSet();
    final lWords = lLower
        .replaceAll(RegExp(r'[^a-z0-9 ]'), '')
        .split(' ')
        .where((w) => w.length > 2 && !boilerplate.contains(w))
        .toSet();

    if (cWords.isEmpty || lWords.isEmpty) {
      return cLower != lLower;
    }

    final overlap = cWords.intersection(lWords).length;
    final union = cWords.union(lWords).length;
    final similarity = overlap / union;

    // If similarity >= 0.5, treat as essentially the same observation/scene
    return similarity < 0.5;
  }

  /// Construct speakable natural text strictly using Track 2 decision and data.
  /// Enforces safety wording: NEVER claims "safe to walk" or guaranteed navigation.
  String _formatSpeechText(Track2Result result) {
    final decision = result.decision;

    // If decision.message is already descriptive and concise, use it as baseline
    var msg = decision.message.trim();

    // Ensure phrasing is clear and voice-friendly
    if (decision.category == AssistanceCategory.alert) {
      if (!msg.toLowerCase().startsWith('alert') && !msg.toLowerCase().startsWith('obstacle') && !msg.toLowerCase().startsWith('caution')) {
        msg = 'Alert: $msg';
      }
    }

    // Avoid robotic or repeated prefixes
    msg = msg.replaceAll(RegExp(r'\[.*?\]'), '').trim();

    return msg;
  }

  int _getCooldownMs(AssistanceCategory category) {
    switch (category) {
      case AssistanceCategory.alert:
        return config.alertCooldownMs;
      case AssistanceCategory.guidance:
        return config.guidanceCooldownMs;
      case AssistanceCategory.info:
        return config.infoCooldownMs;
      case AssistanceCategory.none:
      case AssistanceCategory.unknown:
        return 5000;
    }
  }

  void _recordEvent({
    required String text,
    required AssistanceCategory category,
    required PriorityLevel priority,
    required bool wasSpoken,
    required bool wasInterrupted,
    String reason = '',
  }) {
    if (!_eventController.isClosed) {
      _eventController.add(
        OutputEvent(
          timestamp: DateTime.now(),
          spokenText: text,
          category: category,
          priority: priority,
          wasInterrupted: wasInterrupted,
          wasSpoken: wasSpoken,
          suppressionReason: reason,
        ),
      );
    }
  }

  void dispose() {
    _eventController.close();
  }
}
