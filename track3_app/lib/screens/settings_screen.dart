import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../config/app_config.dart';
import '../presentation/ui_mode_controller.dart';
import '../services/session_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_spacing.dart';
import '../theme/app_typography.dart';
import 'onboarding_screen.dart';

/// Grouped, accessible settings screen covering Voice, Haptics,
/// Network Bridge Connection, Accessibility, and Developer Mode.
class SettingsScreen extends StatefulWidget {
  final AppConfig config;
  final SessionService sessionService;
  final UiModeController uiModeController;

  const SettingsScreen({
    super.key,
    required this.config,
    required this.sessionService,
    required this.uiModeController,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _urlController;
  bool _testingConnection = false;
  String? _testResult;
  bool? _testSuccess;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.config.backendBaseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _testingConnection = true;
      _testResult = null;
      _testSuccess = null;
    });

    widget.config.updateBackendBaseUrl(_urlController.text);
    final stopwatch = Stopwatch()..start();
    try {
      final health = await widget.sessionService.apiService.checkHealth();
      stopwatch.stop();
      if (!mounted) return;
      setState(() {
        _testSuccess = true;
        _testResult = 'Connected to Track 2 Bridge\n'
            '• URL: ${widget.config.backendBaseUrl}\n'
            '• Status: ${health.isHealthy ? "HEALTHY" : "DEGRADED"}\n'
            '• VLM Mode: ${health.vlmMode.toUpperCase()}\n'
            '• Ping: ${stopwatch.elapsedMilliseconds}ms';
      });
      await widget.sessionService.checkBackendHealth();
    } catch (e) {
      stopwatch.stop();
      if (!mounted) return;
      setState(() {
        _testSuccess = false;
        _testResult = 'Connection Failed (${stopwatch.elapsedMilliseconds}ms)\n'
            '• Error: $e';
      });
    } finally {
      if (mounted) {
        setState(() => _testingConnection = false);
      }
    }
  }

  void _testVoice() {
    widget.sessionService.speechService.speak(
      'This is A-Eye guidance voice at current speech rate and pitch.',
      interrupt: true,
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.uiModeController,
      builder: (context, _) {
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('Settings'),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded),
              tooltip: 'Back to Guidance',
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          body: ListView(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.md),
            children: [
              // 1. VOICE & SPEECH
              _SettingsSectionHeader(title: 'Voice & Speech', icon: Icons.record_voice_over_rounded),
              _SettingsCard(
                children: [
                  ListTile(
                    title: const Text('Speech Rate'),
                    subtitle: Text('${(widget.config.ttsSpeechRate * 100).toInt()}% speed'),
                    trailing: SizedBox(
                      width: 140,
                      child: Slider(
                        value: widget.config.ttsSpeechRate,
                        min: 0.25,
                        max: 1.0,
                        divisions: 6,
                        activeColor: AppColors.primary,
                        onChanged: (val) {
                          setState(() => widget.config.updateTtsSpeechRate(val));
                        },
                      ),
                    ),
                  ),
                  const Divider(height: 1),
                  Padding(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    child: OutlinedButton.icon(
                      onPressed: _testVoice,
                      icon: const Icon(Icons.volume_up_rounded, size: 18),
                      label: const Text('Test Voice Output'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.primary,
                        side: const BorderSide(color: AppColors.primary),
                        shape: RoundedRectangleBorder(borderRadius: AppSpacing.roundedMd),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),

              // 2. HAPTICS & TACTILE FEEDBACK
              _SettingsSectionHeader(title: 'Tactile Feedback', icon: Icons.vibration_rounded),
              _SettingsCard(
                children: [
                  SwitchListTile(
                    title: const Text('Vibration Alerts'),
                    subtitle: const Text('Tactile buzz for hazards and path guidance'),
                    value: widget.config.hapticsEnabled,
                    onChanged: (val) {
                      if (val) HapticFeedback.mediumImpact();
                      setState(() => widget.config.updateHapticsEnabled(val));
                    },
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),

              // 3. BACKEND BRIDGE CONNECTION
              _SettingsSectionHeader(title: 'Server Connection', icon: Icons.lan_rounded),
              _SettingsCard(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Specify the network address of the Python Track 2 Bridge.',
                          style: AppTypography.bodySmall,
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        TextField(
                          controller: _urlController,
                          decoration: InputDecoration(
                            labelText: 'Bridge Base URL',
                            hintText: 'http://10.18.185.180:5000',
                            border: OutlineInputBorder(borderRadius: AppSpacing.roundedMd),
                            prefixIcon: const Icon(Icons.link_rounded),
                          ),
                          onChanged: (val) => widget.config.updateBackendBaseUrl(val),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        Wrap(
                          spacing: 8,
                          runSpacing: 4,
                          children: [
                            ActionChip(
                              label: const Text('10.0.2.2 (Emulator)'),
                              onPressed: () {
                                _urlController.text = 'http://10.0.2.2:5000';
                                widget.config.updateBackendBaseUrl(_urlController.text);
                              },
                            ),
                            ActionChip(
                              label: const Text('127.0.0.1 (Local)'),
                              onPressed: () {
                                _urlController.text = 'http://127.0.0.1:5000';
                                widget.config.updateBackendBaseUrl(_urlController.text);
                              },
                            ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.md),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: _testingConnection ? null : _testConnection,
                            icon: _testingConnection
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                  )
                                : const Icon(Icons.network_check_rounded),
                            label: const Text('Test Connection'),
                            style: FilledButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              shape: RoundedRectangleBorder(borderRadius: AppSpacing.roundedMd),
                            ),
                          ),
                        ),
                        if (_testResult != null) ...[
                          const SizedBox(height: AppSpacing.md),
                          Container(
                            padding: const EdgeInsets.all(AppSpacing.md),
                            decoration: BoxDecoration(
                              color: (_testSuccess ?? false)
                                  ? AppColors.primary.withValues(alpha: 0.1)
                                  : AppColors.hazard.withValues(alpha: 0.1),
                              borderRadius: AppSpacing.roundedSm,
                              border: Border.all(
                                color: (_testSuccess ?? false) ? AppColors.primary : AppColors.hazard,
                              ),
                            ),
                            child: Text(
                              _testResult!,
                              style: TextStyle(
                                color: (_testSuccess ?? false) ? AppColors.safeNeutral : AppColors.hazard,
                                fontSize: 13,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),

              // 4. SAMPLING & PROCESSING
              _SettingsSectionHeader(title: 'Camera Sampling Interval', icon: Icons.shutter_speed_rounded),
              _SettingsCard(
                children: [
                  ListTile(
                    title: const Text('Frame Interval'),
                    subtitle: Text('${widget.config.samplingIntervalMs} ms between frame snapshots'),
                    trailing: DropdownButton<int>(
                      value: widget.config.samplingIntervalMs,
                      dropdownColor: AppColors.surfaceCard,
                      items: const [
                        DropdownMenuItem(value: 500, child: Text('500 ms (Fast)')),
                        DropdownMenuItem(value: 750, child: Text('750 ms (Default)')),
                        DropdownMenuItem(value: 1000, child: Text('1000 ms (Balanced)')),
                        DropdownMenuItem(value: 1500, child: Text('1500 ms (Low power)')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setState(() => widget.config.updateSamplingInterval(val));
                        }
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),

              // 5. ACCESSIBILITY OPTIONS
              _SettingsSectionHeader(title: 'Accessibility', icon: Icons.accessibility_new_rounded),
              _SettingsCard(
                children: [
                  SwitchListTile(
                    title: const Text('High Contrast Palette'),
                    subtitle: const Text('Maximum visibility black, gold, and white contrast'),
                    value: widget.uiModeController.isHighContrastEnabled,
                    onChanged: (val) {
                      widget.uiModeController.setHighContrast(val);
                    },
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.school_rounded, color: AppColors.primary),
                    title: const Text('Replay Introduction Tutorial'),
                    subtitle: const Text('Re-listen to the safety notice and gestures guide'),
                    trailing: const Icon(Icons.chevron_right_rounded),
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => OnboardingScreen(
                            uiModeController: widget.uiModeController,
                            speechService: widget.sessionService.speechService,
                            onComplete: () => Navigator.of(context).pop(),
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),

              // 6. DEVELOPER MODE
              _SettingsSectionHeader(title: 'Developer Diagnostics', icon: Icons.code_rounded),
              _SettingsCard(
                children: [
                  SwitchListTile(
                    title: const Text('Developer Mode'),
                    subtitle: const Text('Show HUD with latency, dropped frames, and corridor overlays'),
                    value: widget.uiModeController.isDeveloperModeEnabled,
                    onChanged: (val) {
                      widget.uiModeController.setDeveloperMode(val);
                    },
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xxl),
            ],
          ),
        );
      },
    );
  }
}

class _SettingsSectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;

  const _SettingsSectionHeader({required this.title, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: AppSpacing.xs),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.primary),
          const SizedBox(width: AppSpacing.xs),
          Text(
            title.toUpperCase(),
            style: AppTypography.labelSmall.copyWith(
              color: AppColors.primary,
              letterSpacing: 1.2,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsCard extends StatelessWidget {
  final List<Widget> children;

  const _SettingsCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceElevated,
        borderRadius: AppSpacing.roundedLg,
        border: Border.all(color: AppColors.borderHairline, width: 1),
      ),
      child: ClipRRect(
        borderRadius: AppSpacing.roundedLg,
        child: Column(
          children: children,
        ),
      ),
    );
  }
}
