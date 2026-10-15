import 'package:flutter/material.dart';

import '../output/assistance_output_policy.dart';
import '../state/session_state.dart';

/// Card showing latest spoken guidance and recent history for sighted testing/debugging.
class TranscriptCard extends StatelessWidget {
  final SessionState state;
  final List<OutputEvent> recentEvents;

  const TranscriptCard({
    super.key,
    required this.state,
    required this.recentEvents,
  });

  @override
  Widget build(BuildContext context) {
    final latestResult = state.latestResult;
    final lastSpoken = state.lastSpokenMessage.isNotEmpty
        ? state.lastSpokenMessage
        : (latestResult != null ? latestResult.decision.message : 'No guidance spoken yet.');

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.volume_up, size: 20, color: Colors.teal),
                const SizedBox(width: 8),
                const Text(
                  'Latest Guidance Spoken',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                if (latestResult != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: _getCategoryColor(latestResult.decision.category),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      latestResult.decision.category.toDisplayString(),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Semantics(
              label: 'Last spoken guidance: $lastSpoken',
              child: Text(
                lastSpoken,
                style: const TextStyle(fontSize: 16, height: 1.3),
              ),
            ),
            if (state.schedulerStats != null) ...[
              const Divider(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Processed: ${state.schedulerStats!.processedFrames} frames',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                  Text(
                    'Dropped: ${state.schedulerStats!.droppedFrames}',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                  Text(
                    'Latency: ${state.schedulerStats!.lastLatencyMs}ms',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getCategoryColor(dynamic category) {
    switch (category.toString().split('.').last.toLowerCase()) {
      case 'alert':
        return Colors.red.shade700;
      case 'guidance':
        return Colors.amber.shade800;
      case 'info':
        return Colors.blue.shade700;
      default:
        return Colors.grey.shade600;
    }
  }
}
