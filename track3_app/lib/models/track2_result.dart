import 'assistance_decision.dart';
import 'context_analysis.dart';
import 'perception_result.dart';
import 'spatial_analysis.dart';

/// Final structured result exported by Track 2 to Track 3.
class Track2Result {
  final String frameId;
  final int timestampMs;
  final AssistanceDecision decision;
  final PerceptionResult perception;
  final SpatialAnalysis spatial;
  final ContextAnalysis context;
  final String summary;

  const Track2Result({
    required this.frameId,
    required this.timestampMs,
    required this.decision,
    required this.perception,
    required this.spatial,
    required this.context,
    required this.summary,
  });

  factory Track2Result.fromJson(Map<String, dynamic> json) {
    return Track2Result(
      frameId: json['frame_id']?.toString() ?? '',
      timestampMs: (json['timestamp_ms'] as num?)?.toInt() ?? 0,
      decision: AssistanceDecision.fromJson(json['decision'] as Map<String, dynamic>? ?? {}),
      perception: PerceptionResult.fromJson(json['perception'] as Map<String, dynamic>? ?? {}),
      spatial: SpatialAnalysis.fromJson(json['spatial'] as Map<String, dynamic>? ?? {}),
      context: ContextAnalysis.fromJson(json['context'] as Map<String, dynamic>? ?? {}),
      summary: json['summary']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'frame_id': frameId,
        'timestamp_ms': timestampMs,
        'decision': decision.toJson(),
        'perception': perception.toJson(),
        'spatial': spatial.toJson(),
        'context': context.toJson(),
        'summary': summary,
      };
}
