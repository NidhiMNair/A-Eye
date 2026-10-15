import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import '../camera/camera_service.dart';
import '../config/app_config.dart';
import '../models/models.dart';
import 'track2_api_service.dart';

/// Performance and health metrics for the frame scheduler.
class SchedulerStats {
  final int totalSampledTicks;
  final int processedFrames;
  final int droppedFrames;
  final int lastLatencyMs;
  final bool isCurrentlyInferring;

  const SchedulerStats({
    required this.totalSampledTicks,
    required this.processedFrames,
    required this.droppedFrames,
    required this.lastLatencyMs,
    required this.isCurrentlyInferring,
  });

  SchedulerStats copyWith({
    int? totalSampledTicks,
    int? processedFrames,
    int? droppedFrames,
    int? lastLatencyMs,
    bool? isCurrentlyInferring,
  }) {
    return SchedulerStats(
      totalSampledTicks: totalSampledTicks ?? this.totalSampledTicks,
      processedFrames: processedFrames ?? this.processedFrames,
      droppedFrames: droppedFrames ?? this.droppedFrames,
      lastLatencyMs: lastLatencyMs ?? this.lastLatencyMs,
      isCurrentlyInferring: isCurrentlyInferring ?? this.isCurrentlyInferring,
    );
  }
}

/// Schedules periodic frame capture, buffers the latest frame, and prevents
/// inference pileup by discarding stale frames during active inference.
class FrameScheduler {
  final CameraService cameraService;
  final Track2ApiService apiService;
  final AppConfig config;
  final Uuid _uuid;

  Timer? _timer;
  bool _isRunning = false;
  bool _isInferring = false;
  int _totalTicks = 0;
  int _processedFrames = 0;
  int _droppedFrames = 0;
  int _lastLatencyMs = 0;

  final StreamController<Track2Result> _resultController = StreamController<Track2Result>.broadcast();
  final StreamController<String> _errorController = StreamController<String>.broadcast();
  final StreamController<SchedulerStats> _statsController = StreamController<SchedulerStats>.broadcast();

  // Sliding buffer for multi-frame temporal context support
  final List<Uint8List> _recentFrameBuffer = [];
  final int _maxBufferedFrames = 2;

  FrameScheduler({
    required this.cameraService,
    required this.apiService,
    required this.config,
    Uuid? uuid,
  }) : _uuid = uuid ?? const Uuid();

  bool get isRunning => _isRunning;
  bool get isInferring => _isInferring;

  Stream<Track2Result> get results => _resultController.stream;
  Stream<String> get errors => _errorController.stream;
  Stream<SchedulerStats> get stats => _statsController.stream;

  SchedulerStats get currentStats => SchedulerStats(
        totalSampledTicks: _totalTicks,
        processedFrames: _processedFrames,
        droppedFrames: _droppedFrames,
        lastLatencyMs: _lastLatencyMs,
        isCurrentlyInferring: _isInferring,
      );

  /// Start the continuous sampling timer loop.
  void start() {
    if (_isRunning) return;
    _isRunning = true;
    _recentFrameBuffer.clear();

    _emitStats();

    _timer?.cancel();
    _timer = Timer.periodic(
      Duration(milliseconds: config.samplingIntervalMs),
      (_) => _onTick(),
    );

    if (config.verboseLogging) {
      debugPrint('FrameScheduler started: interval=${config.samplingIntervalMs}ms');
    }
  }

  /// Stop sampling and release timers.
  void stop() {
    if (!_isRunning) return;
    _isRunning = false;
    _timer?.cancel();
    _timer = null;
    _isInferring = false;
    _recentFrameBuffer.clear();

    _emitStats();

    if (config.verboseLogging) {
      debugPrint('FrameScheduler stopped: processed=$_processedFrames, dropped=$_droppedFrames');
    }
  }

  /// Single tick of the sampling loop.
  Future<void> _onTick() async {
    if (!_isRunning) return;
    _totalTicks++;

    // Strict non-overlapping enforcement:
    // If backend inference is currently in-flight, discard/skip frame to prevent queue pile-up.
    if (_isInferring) {
      _droppedFrames++;
      if (config.verboseLogging) {
        debugPrint('FrameScheduler: Inference in progress. Dropped stale tick #$_totalTicks.');
      }
      _emitStats();
      return;
    }

    _isInferring = true;
    _emitStats();

    final stopwatch = Stopwatch()..start();
    try {
      final frameBytes = await cameraService.captureFrameJpeg(
        quality: config.jpegQuality,
      );

      if (frameBytes == null || frameBytes.isEmpty) {
        // Camera unavailable or still initializing; skip without incrementing drop count
        _isInferring = false;
        _emitStats();
        return;
      }

      // Add to sliding frame buffer
      _recentFrameBuffer.add(frameBytes);
      if (_recentFrameBuffer.length > _maxBufferedFrames) {
        _recentFrameBuffer.removeAt(0);
      }

      final frameId = 'f_${DateTime.now().millisecondsSinceEpoch}_${_uuid.v4().substring(0, 8)}';
      final timestampMs = DateTime.now().millisecondsSinceEpoch;

      final result = await apiService.processFrames(
        frameBytesList: List.unmodifiable(_recentFrameBuffer),
        frameId: frameId,
        timestampMs: timestampMs,
      );

      _processedFrames++;
      stopwatch.stop();
      _lastLatencyMs = stopwatch.elapsedMilliseconds;

      if (!_resultController.isClosed) {
        _resultController.add(result);
      }
    } on Track2NetworkException catch (netErr) {
      stopwatch.stop();
      _lastLatencyMs = stopwatch.elapsedMilliseconds;
      if (!_errorController.isClosed) {
        _errorController.add('Backend connection error: ${netErr.message}');
      }
    } on Track2VlmException catch (vlmErr) {
      stopwatch.stop();
      _lastLatencyMs = stopwatch.elapsedMilliseconds;
      if (!_errorController.isClosed) {
        _errorController.add('Vision processing error: ${vlmErr.message}');
      }
    } catch (err) {
      stopwatch.stop();
      _lastLatencyMs = stopwatch.elapsedMilliseconds;
      if (!_errorController.isClosed) {
        _errorController.add('Unexpected processing error: $err');
      }
    } finally {
      _isInferring = false;
      _emitStats();
    }
  }

  void _emitStats() {
    if (!_statsController.isClosed) {
      _statsController.add(currentStats);
    }
  }

  /// Clean up streams and resources.
  void dispose() {
    stop();
    _resultController.close();
    _errorController.close();
    _statsController.close();
  }
}
