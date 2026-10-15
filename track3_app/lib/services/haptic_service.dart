import 'package:flutter/services.dart';
import 'package:vibration/vibration.dart';

import '../config/app_config.dart';

/// Service managing device haptic feedback and vibrations.
class HapticService {
  final AppConfig config;
  bool _hasVibrator = false;
  bool _hasCustomVibrations = false;
  bool _checkedHardware = false;

  int _lastVibrationTimestamp = 0;
  static const int _minVibrationCooldownMs = 1200;

  HapticService({required this.config});

  /// Check hardware vibration capabilities.
  Future<void> checkCapabilities() async {
    if (_checkedHardware) return;
    try {
      _hasVibrator = (await Vibration.hasVibrator()) == true;
      _hasCustomVibrations = (await Vibration.hasCustomVibrationsSupport()) == true;
    } catch (_) {
      _hasVibrator = false;
      _hasCustomVibrations = false;
    } finally {
      _checkedHardware = true;
    }
  }

  /// Strong / urgent vibration pattern for HIGH alerts.
  Future<void> vibrateAlert() async {
    if (!config.hapticsEnabled || !_canVibrate()) return;
    _lastVibrationTimestamp = DateTime.now().millisecondsSinceEpoch;

    try {
      if (_hasVibrator) {
        if (_hasCustomVibrations) {
          // Double buzz alert pattern: 400ms on, 150ms pause, 400ms on
          await Vibration.vibrate(pattern: [0, 400, 150, 400], intensities: [0, 255, 0, 255]);
        } else {
          await Vibration.vibrate(duration: 600);
        }
      } else {
        await HapticFeedback.heavyImpact();
      }
    } catch (_) {
      // Fallback gracefully
      try {
        await HapticFeedback.heavyImpact();
      } catch (_) {}
    }
  }

  /// Medium vibration for GUIDANCE.
  Future<void> vibrateGuidance() async {
    if (!config.hapticsEnabled || !_canVibrate()) return;
    _lastVibrationTimestamp = DateTime.now().millisecondsSinceEpoch;

    try {
      if (_hasVibrator) {
        await Vibration.vibrate(duration: 250);
      } else {
        await HapticFeedback.mediumImpact();
      }
    } catch (_) {
      try {
        await HapticFeedback.mediumImpact();
      } catch (_) {}
    }
  }

  /// Subtle click for INFO or interaction events.
  Future<void> vibrateInfo() async {
    if (!config.hapticsEnabled || !_canVibrate()) return;
    _lastVibrationTimestamp = DateTime.now().millisecondsSinceEpoch;

    try {
      if (_hasVibrator) {
        await Vibration.vibrate(duration: 80);
      } else {
        await HapticFeedback.lightImpact();
      }
    } catch (_) {
      try {
        await HapticFeedback.lightImpact();
      } catch (_) {}
    }
  }

  bool _canVibrate() {
    final now = DateTime.now().millisecondsSinceEpoch;
    return (now - _lastVibrationTimestamp) > _minVibrationCooldownMs;
  }
}
