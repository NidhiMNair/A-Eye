import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';

/// Service managing hardware screen curtain for A-Eye Mode:
/// - Pure black surface (#000000) for zero OLED power emission
/// - Native window brightness dimming to 0.01 (minimizing LCD backlights)
/// - Wake-lock to keep camera and inference pipeline alive
/// - Immersive sticky mode (hides system status and navigation bars)
/// - Automatic restoration on app pause, backgrounding, lock screen, or exit
class ScreenCurtainService with WidgetsBindingObserver {
  static const MethodChannel _channel = MethodChannel('com.aeye.track3_app/screen_curtain');

  bool _isCurtainActive = false;
  final MethodChannel? _overrideChannel;

  ScreenCurtainService({MethodChannel? channel}) : _overrideChannel = channel {
    WidgetsBinding.instance.addObserver(this);
  }

  MethodChannel get channel => _overrideChannel ?? _channel;
  bool get isCurtainActive => _isCurtainActive;

  /// Activate A-Eye Mode screen curtain.
  Future<void> enable() async {
    if (_isCurtainActive) return;

    try {
      // 1. Hide status & navigation bars
      await SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);

      // 2. Invoke native brightness dimming and wake-lock
      await channel.invokeMethod<bool>('enableCurtain');
      _isCurtainActive = true;
    } catch (e) {
      debugPrint('ScreenCurtainService: enable error (platform fallback): $e');
      _isCurtainActive = true; // Still allow Flutter UI layer to render black surface
    }
  }

  /// Deactivate A-Eye Mode screen curtain and restore standard system settings.
  Future<void> disable() async {
    if (!_isCurtainActive) return;

    try {
      // 1. Restore edge-to-edge system bars
      await SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);

      // 2. Restore system brightness and release wake lock
      await channel.invokeMethod<bool>('disableCurtain');
    } catch (e) {
      debugPrint('ScreenCurtainService: disable error: $e');
    } finally {
      _isCurtainActive = false;
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // If phone call arrives or user backgrounds app, restore brightness immediately
    if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive || state == AppLifecycleState.detached) {
      if (_isCurtainActive) {
        disable();
      }
    }
  }

  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    if (_isCurtainActive) {
      disable();
    }
  }
}
