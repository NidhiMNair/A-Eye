import 'package:flutter/foundation.dart';

/// Runtime configuration for A-Eye Track 3 application.
class AppConfig extends ChangeNotifier {
  AppConfig({
    String? backendBaseUrl,
    int? samplingIntervalMs,
    int? jpegQuality,
    int? alertCooldownMs,
    int? guidanceCooldownMs,
    int? infoCooldownMs,
    bool? hapticsEnabled,
    bool? verboseLogging,
    String? ttsLanguage,
    double? ttsSpeechRate,
    int? connectTimeoutMs,
    int? responseTimeoutMs,
    int? maxConsecutiveFailures,
    int? maxBackoffMs,
  })  : _backendBaseUrl = backendBaseUrl ?? defaultBackendUrl,
        _samplingIntervalMs = samplingIntervalMs ?? 750,
        _jpegQuality = jpegQuality ?? 75,
        _alertCooldownMs = alertCooldownMs ?? 3000,
        _guidanceCooldownMs = guidanceCooldownMs ?? 5000,
        _infoCooldownMs = infoCooldownMs ?? 8000,
        _hapticsEnabled = hapticsEnabled ?? true,
        _verboseLogging = verboseLogging ?? kDebugMode,
        _ttsLanguage = ttsLanguage ?? 'en-IN',
        _ttsSpeechRate = ttsSpeechRate ?? 0.5,
        _connectTimeoutMs = connectTimeoutMs ?? 4000,
        _responseTimeoutMs = responseTimeoutMs ?? 25000,
        _maxConsecutiveFailures = maxConsecutiveFailures ?? 3,
        _maxBackoffMs = maxBackoffMs ?? 8000;

  /// Default backend URL: Android Emulator uses 10.0.2.2, desktop/web uses 127.0.0.1
  static String get defaultBackendUrl {
    const fromDefine = String.fromEnvironment('BACKEND_URL');
    if (fromDefine.isNotEmpty) return fromDefine;

    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:5000';
    }
    return 'http://127.0.0.1:5000';
  }

  String _backendBaseUrl;
  int _samplingIntervalMs;
  final int _jpegQuality;
  final int _alertCooldownMs;
  final int _guidanceCooldownMs;
  final int _infoCooldownMs;
  bool _hapticsEnabled;
  final bool _verboseLogging;
  String _ttsLanguage;
  double _ttsSpeechRate;
  final int _connectTimeoutMs;
  int _responseTimeoutMs;
  final int _maxConsecutiveFailures;
  final int _maxBackoffMs;

  String get backendBaseUrl => _backendBaseUrl;
  int get samplingIntervalMs => _samplingIntervalMs;
  int get jpegQuality => _jpegQuality;
  int get alertCooldownMs => _alertCooldownMs;
  int get guidanceCooldownMs => _guidanceCooldownMs;
  int get infoCooldownMs => _infoCooldownMs;
  bool get hapticsEnabled => _hapticsEnabled;
  bool get verboseLogging => _verboseLogging;
  String get ttsLanguage => _ttsLanguage;
  double get ttsSpeechRate => _ttsSpeechRate;
  int get connectTimeoutMs => _connectTimeoutMs;
  int get responseTimeoutMs => _responseTimeoutMs;
  int get maxConsecutiveFailures => _maxConsecutiveFailures;
  int get maxBackoffMs => _maxBackoffMs;

  void updateBackendBaseUrl(String newUrl) {
    var trimmed = newUrl.trim();
    if (trimmed.endsWith('/')) {
      trimmed = trimmed.substring(0, trimmed.length - 1);
    }
    if (_backendBaseUrl != trimmed) {
      _backendBaseUrl = trimmed;
      notifyListeners();
    }
  }

  void updateSamplingInterval(int intervalMs) {
    if (intervalMs >= 300 && intervalMs <= 5000 && _samplingIntervalMs != intervalMs) {
      _samplingIntervalMs = intervalMs;
      notifyListeners();
    }
  }

  void updateResponseTimeout(int timeoutMs) {
    if (timeoutMs >= 5000 && timeoutMs <= 60000 && _responseTimeoutMs != timeoutMs) {
      _responseTimeoutMs = timeoutMs;
      notifyListeners();
    }
  }

  void updateHapticsEnabled(bool enabled) {
    if (_hapticsEnabled != enabled) {
      _hapticsEnabled = enabled;
      notifyListeners();
    }
  }

  void updateTtsLanguage(String lang) {
    if (_ttsLanguage != lang) {
      _ttsLanguage = lang;
      notifyListeners();
    }
  }

  void updateTtsSpeechRate(double rate) {
    if (_ttsSpeechRate != rate) {
      _ttsSpeechRate = rate;
      notifyListeners();
    }
  }
}
