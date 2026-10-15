import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../services/session_service.dart';

/// Developer and user settings screen for Track 3 configuration.
class SettingsScreen extends StatefulWidget {
  final AppConfig config;
  final SessionService sessionService;

  const SettingsScreen({
    super.key,
    required this.config,
    required this.sessionService,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _urlController;
  bool _testingConnection = false;
  String? _testResult;

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
    });

    widget.config.updateBackendBaseUrl(_urlController.text);
    try {
      final health = await widget.sessionService.apiService.checkHealth();
      if (!mounted) return;
      setState(() {
        _testResult = 'Success! Connected to Track 2 Bridge (Mode: ${health.vlmMode.toUpperCase()})';
      });
      await widget.sessionService.checkBackendHealth();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _testResult = 'Connection Failed: $e';
      });
    } finally {
      if (mounted) {
        setState(() => _testingConnection = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings & Configuration'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Backend Bridge URL',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          const Text(
            'Specify the network address of the Python Track 2 Bridge.',
            style: TextStyle(fontSize: 13, color: Colors.grey),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _urlController,
            decoration: const InputDecoration(
              labelText: 'Bridge Base URL',
              hintText: 'http://10.0.2.2:5000 or http://192.168.x.x:5000',
              border: OutlineInputBorder(),
              prefixIcon: Icon(Icons.lan),
            ),
            onChanged: (val) => widget.config.updateBackendBaseUrl(val),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: [
              ActionChip(
                label: const Text('Android Emulator (10.0.2.2)'),
                onPressed: () {
                  _urlController.text = 'http://10.0.2.2:5000';
                  widget.config.updateBackendBaseUrl(_urlController.text);
                },
              ),
              ActionChip(
                label: const Text('Localhost (127.0.0.1)'),
                onPressed: () {
                  _urlController.text = 'http://127.0.0.1:5000';
                  widget.config.updateBackendBaseUrl(_urlController.text);
                },
              ),
            ],
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _testingConnection ? null : _testConnection,
            icon: _testingConnection
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.network_check),
            label: const Text('Test Connection'),
          ),
          if (_testResult != null) ...[
            const SizedBox(height: 8),
            Text(
              _testResult!,
              style: TextStyle(
                color: _testResult!.startsWith('Success') ? Colors.green : Colors.red,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
          const Divider(height: 36),
          const Text(
            'Sampling & Processing',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          ListTile(
            title: const Text('Sampling Interval'),
            subtitle: Text('${widget.config.samplingIntervalMs} ms between sampled frames'),
            trailing: DropdownButton<int>(
              value: widget.config.samplingIntervalMs,
              items: const [
                DropdownMenuItem(value: 500, child: Text('500 ms (Fast)')),
                DropdownMenuItem(value: 750, child: Text('750 ms (Default)')),
                DropdownMenuItem(value: 1000, child: Text('1000 ms (Balanced)')),
                DropdownMenuItem(value: 1500, child: Text('1500 ms (Conservative)')),
              ],
              onChanged: (val) {
                if (val != null) {
                  setState(() => widget.config.updateSamplingInterval(val));
                }
              },
            ),
          ),
          const Divider(height: 36),
          const Text(
            'Feedback & Output',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SwitchListTile(
            title: const Text('Haptic Feedback (Vibration)'),
            subtitle: const Text('Vibrate on high-priority alerts and directional guidance'),
            value: widget.config.hapticsEnabled,
            onChanged: (val) => setState(() => widget.config.updateHapticsEnabled(val)),
          ),
          ListTile(
            title: const Text('Speech Rate'),
            subtitle: Text('${(widget.config.ttsSpeechRate * 100).toInt()}%'),
            trailing: SizedBox(
              width: 150,
              child: Slider(
                value: widget.config.ttsSpeechRate,
                min: 0.25,
                max: 1.0,
                divisions: 6,
                onChanged: (val) => setState(() => widget.config.updateTtsSpeechRate(val)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
