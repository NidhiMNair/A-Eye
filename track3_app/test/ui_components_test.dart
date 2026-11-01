import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/models/assistance_category.dart';
import 'package:track3_app/services/frame_scheduler.dart';
import 'package:track3_app/state/session_state.dart';
import 'package:track3_app/theme/app_theme.dart';
import 'package:track3_app/widgets/guidance_sheet.dart';
import 'package:track3_app/widgets/mode_switch_pill.dart';
import 'package:track3_app/widgets/severity_badge.dart';
import 'package:track3_app/widgets/status_capsule.dart';
import 'package:track3_app/widgets/tactile_action_button.dart';

void main() {
  Widget wrapWidget(Widget child, {bool highContrast = false, double textScale = 1.0}) {
    return MaterialApp(
      theme: AppTheme.buildTheme(highContrast: highContrast),
      home: Scaffold(
        body: MediaQuery(
          data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
          child: child,
        ),
      ),
    );
  }

  group('TactileActionButton Widget Tests', () {
    testWidgets('Renders idle START ASSISTANCE and triggers onStart callback', (tester) async {
      var started = false;
      var stopped = false;

      await tester.pumpWidget(
        wrapWidget(
          TactileActionButton(
            status: AssistanceStatus.idle,
            onStart: () => started = true,
            onStop: () => stopped = true,
          ),
        ),
      );

      expect(find.text('START ASSISTANCE'), findsOneWidget);
      expect(find.byIcon(Icons.play_arrow_rounded), findsOneWidget);

      await tester.tap(find.text('START ASSISTANCE'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(started, isTrue);
      expect(stopped, isFalse);
    });

    testWidgets('Renders active PAUSE ASSISTANCE and triggers onStop callback', (tester) async {
      var started = false;
      var stopped = false;

      await tester.pumpWidget(
        wrapWidget(
          TactileActionButton(
            status: AssistanceStatus.cameraReady,
            onStart: () => started = true,
            onStop: () => stopped = true,
          ),
        ),
      );

      expect(find.text('PAUSE ASSISTANCE'), findsOneWidget);
      expect(find.byIcon(Icons.pause_circle_filled_rounded), findsOneWidget);

      await tester.tap(find.text('PAUSE ASSISTANCE'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      expect(stopped, isTrue);
      expect(started, isFalse);
    });

    testWidgets('Renders busy spinner when starting or stopping', (tester) async {
      await tester.pumpWidget(
        wrapWidget(
          TactileActionButton(
            status: AssistanceStatus.starting,
            onStart: () {},
            onStop: () {},
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('STARTING...'), findsOneWidget);
    });
  });

  group('SeverityBadge Widget Tests', () {
    testWidgets('Renders HAZARD with triangle warning icon', (tester) async {
      await tester.pumpWidget(wrapWidget(const SeverityBadge(category: AssistanceCategory.alert)));

      expect(find.text('HAZARD'), findsOneWidget);
      expect(find.byIcon(Icons.warning_rounded), findsOneWidget);
    });

    testWidgets('Renders GUIDANCE with navigation icon', (tester) async {
      await tester.pumpWidget(wrapWidget(const SeverityBadge(category: AssistanceCategory.guidance)));

      expect(find.text('GUIDANCE'), findsOneWidget);
      expect(find.byIcon(Icons.navigation_rounded), findsOneWidget);
    });

    testWidgets('Renders AWARENESS for info category', (tester) async {
      await tester.pumpWidget(wrapWidget(const SeverityBadge(category: AssistanceCategory.info)));

      expect(find.text('AWARENESS'), findsOneWidget);
      expect(find.byIcon(Icons.info_outline_rounded), findsOneWidget);
    });

    testWidgets('Renders CLEAR for none category', (tester) async {
      await tester.pumpWidget(wrapWidget(const SeverityBadge(category: AssistanceCategory.none)));

      expect(find.text('CLEAR'), findsOneWidget);
      expect(find.byIcon(Icons.check_circle_outline_rounded), findsOneWidget);
    });
  });

  group('StatusCapsule Widget Tests', () {
    testWidgets('Displays Ready & Scanning when camera is ready and online', (tester) async {
      const state = SessionState(
        status: AssistanceStatus.cameraReady,
        isBackendOnline: true,
      );

      await tester.pumpWidget(wrapWidget(const StatusCapsule(state: state)));

      expect(find.text('Ready & Scanning'), findsOneWidget);
      expect(find.byIcon(Icons.lens_blur_rounded), findsOneWidget);
    });

    testWidgets('Displays Server Offline badge when backend is unreachable', (tester) async {
      const state = SessionState(
        status: AssistanceStatus.error,
        isBackendOnline: false,
      );

      await tester.pumpWidget(wrapWidget(const StatusCapsule(state: state)));

      expect(find.text('Server Offline'), findsOneWidget);
      expect(find.text('OFFLINE'), findsOneWidget);
    });
  });

  group('ModeSwitchPill Widget Tests', () {
    testWidgets('Switches between Visual and A-Eye Dark mode', (tester) async {
      var selectedMode = false;

      await tester.pumpWidget(
        wrapWidget(
          ModeSwitchPill(
            isAEyeMode: false,
            onModeChanged: (val) => selectedMode = val,
          ),
        ),
      );

      expect(find.text('Visual'), findsOneWidget);
      expect(find.text('A-Eye Dark'), findsOneWidget);

      await tester.tap(find.text('A-Eye Dark'));
      await tester.pumpAndSettle();

      expect(selectedMode, isTrue);
    });
  });

  group('GuidanceSheet Widget Tests & 200% Accessibility Scaling', () {
    testWidgets('Sanitizes stray punctuation and renders at 200% text scale without overflow', (tester) async {
      const state = SessionState(
        status: AssistanceStatus.speaking,
        isBackendOnline: true,
        lastSpokenMessage: 'Cluttered desk surface with cords and small items., keyboard',
      );

      await tester.pumpWidget(
        wrapWidget(
          const GuidanceSheet(
            state: state,
            isDeveloperMode: false,
          ),
          textScale: 2.0, // 200% text scale test!
        ),
      );

      // Verify punctuation was sanitized in display
      expect(find.text('Cluttered desk surface with cords and small items, keyboard'), findsOneWidget);
      expect(tester.takeException(), isNull, reason: 'Must not overflow at 200% text scale');
    });

    testWidgets('Hides telemetry when Developer Mode is disabled, shows when enabled', (tester) async {
      const state = SessionState(
        status: AssistanceStatus.cameraReady,
        isBackendOnline: true,
        lastSpokenMessage: 'Pathway open ahead',
        schedulerStats: SchedulerStats(
          totalSampledTicks: 14,
          processedFrames: 12,
          droppedFrames: 2,
          lastLatencyMs: 850,
          isCurrentlyInferring: false,
        ),
      );

      // 1. Normal user mode: no developer telemetry
      await tester.pumpWidget(
        wrapWidget(const GuidanceSheet(state: state, isDeveloperMode: false)),
      );
      expect(find.textContaining('Latency:'), findsNothing);
      expect(find.textContaining('Dropped:'), findsNothing);

      // 2. Developer mode: telemetry displayed
      await tester.pumpWidget(
        wrapWidget(const GuidanceSheet(state: state, isDeveloperMode: true)),
      );
      expect(find.textContaining('Latency: 850ms'), findsOneWidget);
      expect(find.textContaining('Dropped: 2'), findsOneWidget);
    });
  });
}
