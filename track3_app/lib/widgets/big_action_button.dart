import 'package:flutter/material.dart';

import '../state/session_state.dart';

/// An accessible, prominent touch control for starting and stopping assistance.
class BigActionButton extends StatelessWidget {
  final AssistanceStatus status;
  final VoidCallback onStart;
  final VoidCallback onStop;

  const BigActionButton({
    super.key,
    required this.status,
    required this.onStart,
    required this.onStop,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = status.isActive;
    final isBusy = status == AssistanceStatus.starting || status == AssistanceStatus.stopping;

    final backgroundColor = isActive ? Colors.red.shade700 : Colors.teal.shade700;
    final foregroundColor = Colors.white;

    final label = isActive ? 'STOP ASSISTANCE' : 'START ASSISTANCE';
    final hint = isActive
        ? 'Double tap to stop camera scanning and audio guidance.'
        : 'Double tap to start camera scanning and receive continuous audio guidance.';

    return Semantics(
      button: true,
      enabled: !isBusy,
      label: label,
      hint: hint,
      child: Material(
        color: isBusy ? Colors.grey.shade800 : backgroundColor,
        borderRadius: BorderRadius.circular(24),
        elevation: 6,
        child: InkWell(
          borderRadius: BorderRadius.circular(24),
          onTap: isBusy ? null : (isActive ? onStop : onStart),
          child: Container(
            height: 140,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            alignment: Alignment.center,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isBusy) ...[
                  const CircularProgressIndicator(color: Colors.white, strokeWidth: 4),
                  const SizedBox(width: 20),
                ] else ...[
                  Icon(
                    isActive ? Icons.stop_circle : Icons.play_circle_fill,
                    size: 56,
                    color: foregroundColor,
                  ),
                  const SizedBox(width: 16),
                ],
                Flexible(
                  child: Text(
                    isBusy
                        ? (status == AssistanceStatus.starting ? 'STARTING...' : 'STOPPING...')
                        : label,
                    style: TextStyle(
                      color: foregroundColor,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
