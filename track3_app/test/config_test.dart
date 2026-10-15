import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/config/app_config.dart';

void main() {
  group('12: Configuration Parsing & Updates', () {
    test('Default values are initialized properly', () {
      final config = AppConfig();

      expect(config.backendBaseUrl, isNotEmpty);
      expect(config.samplingIntervalMs, 750);
      expect(config.jpegQuality, 75);
      expect(config.alertCooldownMs, 3000);
      expect(config.guidanceCooldownMs, 5000);
      expect(config.infoCooldownMs, 8000);
      expect(config.hapticsEnabled, isTrue);
      expect(config.ttsLanguage, 'en-IN');
      expect(config.ttsSpeechRate, 0.5);
    });

    test('Custom constructor overrides default settings', () {
      final config = AppConfig(
        backendBaseUrl: 'http://192.168.1.100:5000',
        samplingIntervalMs: 1000,
        hapticsEnabled: false,
        ttsLanguage: 'en-US',
        ttsSpeechRate: 0.6,
      );

      expect(config.backendBaseUrl, 'http://192.168.1.100:5000');
      expect(config.samplingIntervalMs, 1000);
      expect(config.hapticsEnabled, isFalse);
      expect(config.ttsLanguage, 'en-US');
      expect(config.ttsSpeechRate, 0.6);
    });

    test('Mutators update properties and notify listeners', () {
      final config = AppConfig();
      var notificationCount = 0;
      config.addListener(() {
        notificationCount++;
      });

      config.updateBackendBaseUrl('http://custom-ip:8000/');
      expect(config.backendBaseUrl, 'http://custom-ip:8000', reason: 'Trailing slash should be stripped');
      expect(notificationCount, 1);

      config.updateSamplingInterval(1200);
      expect(config.samplingIntervalMs, 1200);
      expect(notificationCount, 2);

      config.updateHapticsEnabled(false);
      expect(config.hapticsEnabled, isFalse);
      expect(notificationCount, 3);
    });
  });
}
