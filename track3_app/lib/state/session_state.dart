import '../models/models.dart';
import '../services/frame_scheduler.dart';

/// Explicit application and assistance session lifecycle states.
enum AssistanceStatus {
  idle,
  starting,
  cameraReady,
  processing,
  speaking,
  error,
  stopping;

  bool get isActive =>
      this == AssistanceStatus.starting ||
      this == AssistanceStatus.cameraReady ||
      this == AssistanceStatus.processing ||
      this == AssistanceStatus.speaking;
}

/// Snapshot of the complete session state for UI presentation.
class SessionState {
  final AssistanceStatus status;
  final String statusMessage;
  final String? errorMessage;
  final Track2Result? latestResult;
  final String lastSpokenMessage;
  final SchedulerStats? schedulerStats;
  final bool isBackendOnline;
  final String backendMode;

  const SessionState({
    this.status = AssistanceStatus.idle,
    this.statusMessage = 'Assistance stopped. Tap Start to begin.',
    this.errorMessage,
    this.latestResult,
    this.lastSpokenMessage = '',
    this.schedulerStats,
    this.isBackendOnline = false,
    this.backendMode = 'unknown',
  });

  SessionState copyWith({
    AssistanceStatus? status,
    String? statusMessage,
    String? errorMessage,
    Track2Result? latestResult,
    String? lastSpokenMessage,
    SchedulerStats? schedulerStats,
    bool? isBackendOnline,
    String? backendMode,
  }) {
    return SessionState(
      status: status ?? this.status,
      statusMessage: statusMessage ?? this.statusMessage,
      errorMessage: errorMessage,
      latestResult: latestResult ?? this.latestResult,
      lastSpokenMessage: lastSpokenMessage ?? this.lastSpokenMessage,
      schedulerStats: schedulerStats ?? this.schedulerStats,
      isBackendOnline: isBackendOnline ?? this.isBackendOnline,
      backendMode: backendMode ?? this.backendMode,
    );
  }
}
