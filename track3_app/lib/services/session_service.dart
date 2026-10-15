import 'dart:async';

import 'package:flutter/foundation.dart';

import '../camera/camera_service.dart';
import '../config/app_config.dart';
import '../models/models.dart';
import '../output/assistance_output_policy.dart';
import '../state/session_state.dart';
import 'frame_scheduler.dart';
import 'haptic_service.dart';
import 'speech_service.dart';
import 'track2_api_service.dart';

/// Orchestrates the end-to-end assistance session lifecycle,
/// linking Camera -> FrameScheduler -> Track2Api -> OutputPolicy -> Speech/Haptics.
class SessionService extends ChangeNotifier {
  final AppConfig config;
  final CameraService cameraService;
  final Track2ApiService apiService;
  final SpeechService speechService;
  final HapticService hapticService;
  late final FrameScheduler frameScheduler;
  late final AssistanceOutputPolicy outputPolicy;

  SessionState _state = const SessionState();
  SessionState get state => _state;

  StreamSubscription<Track2Result>? _resultSub;
  StreamSubscription<String>? _errorSub;
  StreamSubscription<SchedulerStats>? _statsSub;
  StreamSubscription<bool>? _speechSub;
  StreamSubscription<OutputEvent>? _outputEventSub;

  final List<OutputEvent> _recentEvents = [];
  List<OutputEvent> get recentEvents => List.unmodifiable(_recentEvents);

  int _lastErrorSpokenTimestamp = 0;
  static const int _errorSpeechCooldownMs = 10000;

  SessionService({
    required this.config,
    required this.cameraService,
    required this.apiService,
    required this.speechService,
    required this.hapticService,
    FrameScheduler? scheduler,
    AssistanceOutputPolicy? policy,
  }) {
    frameScheduler = scheduler ??
        FrameScheduler(
          cameraService: cameraService,
          apiService: apiService,
          config: config,
        );

    outputPolicy = policy ??
        AssistanceOutputPolicy(
          speechService: speechService,
          hapticService: hapticService,
          config: config,
        );

    _initListeners();
    checkBackendHealth();
  }

  void _initListeners() {
    _speechSub = speechService.speakingStateStream.listen((isSpeaking) {
      if (_state.status.isActive) {
        final newStatus = isSpeaking
            ? AssistanceStatus.speaking
            : (frameScheduler.isInferring ? AssistanceStatus.processing : AssistanceStatus.cameraReady);
        _updateState(_state.copyWith(status: newStatus));
      }
    });

    _resultSub = frameScheduler.results.listen((result) async {
      _updateState(_state.copyWith(
        latestResult: result,
        status: speechService.isSpeaking ? AssistanceStatus.speaking : AssistanceStatus.cameraReady,
        statusMessage: 'Inference complete: ${result.decision.category.toDisplayString()}',
      ));

      await outputPolicy.processResult(result);
    });

    _errorSub = frameScheduler.errors.listen((errorMsg) {
      _updateState(_state.copyWith(
        errorMessage: errorMsg,
        statusMessage: 'Connection warning: $errorMsg',
      ));

      _speakErrorOnce(errorMsg);
    });

    _statsSub = frameScheduler.stats.listen((stats) {
      final status = _state.status;
      if (status.isActive && !speechService.isSpeaking) {
        final newStatus = stats.isCurrentlyInferring
            ? AssistanceStatus.processing
            : AssistanceStatus.cameraReady;
        _updateState(_state.copyWith(
          schedulerStats: stats,
          status: newStatus,
        ));
      } else {
        _updateState(_state.copyWith(schedulerStats: stats));
      }
    });

    _outputEventSub = outputPolicy.events.listen((event) {
      _recentEvents.insert(0, event);
      if (_recentEvents.length > 50) {
        _recentEvents.removeLast();
      }
      if (event.wasSpoken) {
        _updateState(_state.copyWith(lastSpokenMessage: event.spokenText));
      }
      notifyListeners();
    });
  }

  /// Query backend health and update status flags.
  Future<void> checkBackendHealth() async {
    try {
      final health = await apiService.checkHealth();
      _updateState(_state.copyWith(
        isBackendOnline: health.isHealthy,
        backendMode: health.vlmMode,
      ));
    } catch (_) {
      _updateState(_state.copyWith(
        isBackendOnline: false,
        backendMode: 'offline',
      ));
    }
  }

  /// Start continuous navigation assistance session.
  Future<void> startAssistance() async {
    if (_state.status.isActive) return;

    _updateState(_state.copyWith(
      status: AssistanceStatus.starting,
      statusMessage: 'Starting camera and initializing assistance...',
      errorMessage: null,
    ));

    try {
      // 1. Initialize hardware subsystems
      await hapticService.checkCapabilities();
      await speechService.initialize();
      await cameraService.initialize();

      // 2. Reset remote Track 2 context for clean session
      try {
        await apiService.resetSession();
      } catch (e) {
        debugPrint('Warning: remote session reset failed: $e');
      }

      // 3. Reset client-side output policy history
      outputPolicy.reset();

      // 4. Start frame scheduler sampling loop
      frameScheduler.start();

      _updateState(_state.copyWith(
        status: AssistanceStatus.cameraReady,
        statusMessage: 'Assistance active. Scanning surroundings.',
      ));

      // Voice prompt indicating successful start
      await speechService.speak('A-Eye assistance started.', interrupt: true);
    } catch (e) {
      debugPrint('Session start failure: $e');
      _updateState(_state.copyWith(
        status: AssistanceStatus.error,
        statusMessage: 'Could not start assistance.',
        errorMessage: e.toString(),
      ));

      await speechService.speak('Error starting assistance. Please check camera permissions.');
    }
  }

  /// Stop active assistance and release hardware locks.
  Future<void> stopAssistance() async {
    if (_state.status == AssistanceStatus.idle) return;

    _updateState(_state.copyWith(
      status: AssistanceStatus.stopping,
      statusMessage: 'Stopping assistance...',
    ));

    try {
      frameScheduler.stop();
      await speechService.stop();
      await cameraService.dispose();

      _updateState(_state.copyWith(
        status: AssistanceStatus.idle,
        statusMessage: 'Assistance stopped. Tap Start to begin.',
        errorMessage: null,
      ));

      await speechService.speak('Assistance stopped.');
    } catch (e) {
      _updateState(_state.copyWith(
        status: AssistanceStatus.idle,
        statusMessage: 'Assistance stopped.',
        errorMessage: e.toString(),
      ));
    }
  }

  void _speakErrorOnce(String errorMsg) {
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _lastErrorSpokenTimestamp > _errorSpeechCooldownMs) {
      _lastErrorSpokenTimestamp = now;
      speechService.speak('Backend connection warning. Retrying.');
    }
  }

  void _updateState(SessionState newState) {
    _state = newState;
    notifyListeners();
  }

  @override
  void dispose() {
    _resultSub?.cancel();
    _errorSub?.cancel();
    _statsSub?.cancel();
    _speechSub?.cancel();
    _outputEventSub?.cancel();
    frameScheduler.dispose();
    outputPolicy.dispose();
    cameraService.dispose();
    speechService.dispose();
    apiService.dispose();
    super.dispose();
  }
}
