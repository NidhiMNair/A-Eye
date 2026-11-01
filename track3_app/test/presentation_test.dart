import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:track3_app/presentation/display_text_formatter.dart';
import 'package:track3_app/presentation/ui_mode_controller.dart';

void main() {
  group('DisplayTextFormatter Unit Tests', () {
    test('Collapses stray consecutive punctuation (., -> ,)', () {
      const raw = 'Cluttered desk surface with cords and small items., keyboard';
      final formatted = DisplayTextFormatter.formatGuidance(raw);
      expect(formatted, 'Cluttered desk surface with cords and small items, keyboard');
    });

    test('Collapses multiple commas and periods and normalizes whitespace', () {
      const raw = 'obstacle detected,,  ahead ..  watch step :';
      final formatted = DisplayTextFormatter.formatGuidance(raw);
      expect(formatted, 'Obstacle detected, ahead. Watch step');
    });

    test('Ensures first letter capitalization and trims trailing punctuation', () {
      const raw = '   stairs descending on the right , ';
      final formatted = DisplayTextFormatter.formatGuidance(raw);
      expect(formatted, 'Stairs descending on the right');
    });

    test('Handles empty and whitespace-only strings gracefully', () {
      expect(DisplayTextFormatter.formatGuidance(''), '');
      expect(DisplayTextFormatter.formatGuidance('   '), '');
    });

    test('Formats human-friendly status titles without technical jargon', () {
      expect(
        DisplayTextFormatter.formatStatusTitle(
          isSpeaking: false,
          isInferring: false,
          hasError: false,
          isOnline: true,
          categoryDisplay: 'alert',
        ),
        'Hazard Ahead',
      );

      expect(
        DisplayTextFormatter.formatStatusTitle(
          isSpeaking: true,
          isInferring: false,
          hasError: false,
          isOnline: true,
          categoryDisplay: null,
        ),
        'Speaking Guidance',
      );

      expect(
        DisplayTextFormatter.formatStatusTitle(
          isSpeaking: false,
          isInferring: false,
          hasError: true,
          isOnline: false,
          categoryDisplay: null,
        ),
        'Server Offline',
      );
    });
  });

  group('UiModeController Unit Tests', () {
    setUp(() {
      SharedPreferences.setMockInitialValues({});
    });

    test('Initializes with default values and toggles A-Eye Mode', () async {
      final controller = UiModeController();
      await controller.initialize();

      expect(controller.isAEyeModeActive, isFalse);
      expect(controller.isDeveloperModeEnabled, isFalse);
      expect(controller.isHighContrastEnabled, isFalse);
      expect(controller.hasCompletedOnboarding, isFalse);

      var notified = false;
      controller.addListener(() => notified = true);

      controller.setAEyeMode(true);
      expect(controller.isAEyeModeActive, isTrue);
      expect(notified, isTrue);
    });

    test('Persists Developer Mode and High Contrast to SharedPreferences', () async {
      final controller = UiModeController();
      await controller.initialize();

      await controller.setDeveloperMode(true);
      await controller.setHighContrast(true);
      await controller.setOnboardingCompleted(true);

      expect(controller.isDeveloperModeEnabled, isTrue);
      expect(controller.isHighContrastEnabled, isTrue);
      expect(controller.hasCompletedOnboarding, isTrue);

      // Verify second instance loads persisted preferences
      final controller2 = UiModeController();
      await controller2.initialize();

      expect(controller2.isDeveloperModeEnabled, isTrue);
      expect(controller2.isHighContrastEnabled, isTrue);
      expect(controller2.hasCompletedOnboarding, isTrue);
    });
  });
}
