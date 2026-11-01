import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Presentation state controller managing UI modes:
/// 1. A-Eye Mode (OLED dark screen, tactile audio-first mode)
/// 2. Developer Mode (Telemetry HUD, latency stats, bounding boxes)
/// 3. High Contrast Accessibility Mode
/// 4. Onboarding state
class UiModeController extends ChangeNotifier {
  static const String _keyDevMode = 'aeye_pref_developer_mode';
  static const String _keyHighContrast = 'aeye_pref_high_contrast';
  static const String _keyOnboardingDone = 'aeye_pref_onboarding_done';

  bool _isAEyeModeActive = false;
  bool _isDeveloperModeEnabled = false;
  bool _isHighContrastEnabled = false;
  bool _hasCompletedOnboarding = false;
  bool _isInitialized = false;

  SharedPreferences? _prefs;

  UiModeController({SharedPreferences? initialPrefs}) {
    if (initialPrefs != null) {
      _prefs = initialPrefs;
      _loadFromPrefs();
      _isInitialized = true;
    }
  }

  bool get isAEyeModeActive => _isAEyeModeActive;
  bool get isDeveloperModeEnabled => _isDeveloperModeEnabled;
  bool get isHighContrastEnabled => _isHighContrastEnabled;
  bool get hasCompletedOnboarding => _hasCompletedOnboarding;
  bool get isInitialized => _isInitialized;

  Future<void> initialize() async {
    if (_isInitialized) return;
    try {
      _prefs ??= await SharedPreferences.getInstance();
      _loadFromPrefs();
    } catch (e) {
      debugPrint('UiModeController: Failed to load SharedPreferences: $e');
    } finally {
      _isInitialized = true;
      notifyListeners();
    }
  }

  void _loadFromPrefs() {
    final p = _prefs;
    if (p == null) return;
    _isDeveloperModeEnabled = p.getBool(_keyDevMode) ?? false;
    _isHighContrastEnabled = p.getBool(_keyHighContrast) ?? false;
    _hasCompletedOnboarding = p.getBool(_keyOnboardingDone) ?? false;
  }

  /// Toggle A-Eye Mode (pure black, low brightness, gesture-locked tactile operation).
  void setAEyeMode(bool active) {
    if (_isAEyeModeActive == active) return;
    _isAEyeModeActive = active;
    notifyListeners();
  }

  /// Toggle Developer Mode (exposing HUD, latency, frame counts).
  Future<void> setDeveloperMode(bool enabled) async {
    if (_isDeveloperModeEnabled == enabled) return;
    _isDeveloperModeEnabled = enabled;
    notifyListeners();
    await _prefs?.setBool(_keyDevMode, enabled);
  }

  /// Toggle High Contrast palette for low-vision accessibility.
  Future<void> setHighContrast(bool enabled) async {
    if (_isHighContrastEnabled == enabled) return;
    _isHighContrastEnabled = enabled;
    notifyListeners();
    await _prefs?.setBool(_keyHighContrast, enabled);
  }

  /// Mark onboarding completed.
  Future<void> setOnboardingCompleted(bool completed) async {
    if (_hasCompletedOnboarding == completed) return;
    _hasCompletedOnboarding = completed;
    notifyListeners();
    await _prefs?.setBool(_keyOnboardingDone, completed);
  }
}
