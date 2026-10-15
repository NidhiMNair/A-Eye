import 'package:flutter/material.dart';

import '../state/session_state.dart';

/// Status banner showing backend connectivity, active VLM mode, and pipeline state.
class StatusBanner extends StatelessWidget {
  final SessionState state;

  const StatusBanner({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    Color statusColor;
    String statusTitle;
    IconData statusIcon;

    switch (state.status) {
      case AssistanceStatus.idle:
        statusColor = Colors.grey;
        statusTitle = 'IDLE';
        statusIcon = Icons.pause_circle_outline;
        break;
      case AssistanceStatus.starting:
        statusColor = Colors.blue;
        statusTitle = 'INITIALIZING';
        statusIcon = Icons.hourglass_top;
        break;
      case AssistanceStatus.cameraReady:
        statusColor = Colors.green;
        statusTitle = 'SCANNING';
        statusIcon = Icons.camera_alt;
        break;
      case AssistanceStatus.processing:
        statusColor = Colors.teal;
        statusTitle = 'PROCESSING';
        statusIcon = Icons.auto_awesome;
        break;
      case AssistanceStatus.speaking:
        statusColor = Colors.deepOrange;
        statusTitle = 'SPEAKING';
        statusIcon = Icons.record_voice_over;
        break;
      case AssistanceStatus.stopping:
        statusColor = Colors.amber;
        statusTitle = 'STOPPING';
        statusIcon = Icons.hourglass_bottom;
        break;
      case AssistanceStatus.error:
        statusColor = Colors.red;
        statusTitle = 'ERROR';
        statusIcon = Icons.error_outline;
        break;
    }

    final isMock = state.backendMode.contains('mock');
    final isOnline = state.isBackendOnline;

    return Semantics(
      label: 'System status: $statusTitle. Backend: ${isOnline ? "Online" : "Offline"}, Mode: ${state.backendMode}.',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: statusColor.withValues(alpha: 0.5),
            width: 2,
          ),
        ),
        child: Row(
          children: [
            Icon(statusIcon, color: statusColor, size: 28),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    statusTitle,
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.1,
                    ),
                  ),
                  Text(
                    state.statusMessage,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 13),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            // Backend mode chip
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: isOnline ? (isMock ? Colors.amber.shade900 : Colors.green.shade900) : Colors.red.shade900,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                isOnline ? state.backendMode.toUpperCase() : 'OFFLINE',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
