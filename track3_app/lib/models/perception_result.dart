import 'detected_object.dart';

/// Structured perception result produced by Track 2 VLM.
class PerceptionResult {
  final String frameId;
  final int timestampMs;
  final String source;
  final List<DetectedObject> objects;
  final String sceneLabel;
  final String? sceneDescription;
  final List<String> hazards;
  final List<String> uncertainties;

  const PerceptionResult({
    required this.frameId,
    required this.timestampMs,
    required this.source,
    required this.objects,
    required this.sceneLabel,
    this.sceneDescription,
    required this.hazards,
    required this.uncertainties,
  });

  factory PerceptionResult.fromJson(Map<String, dynamic> json) {
    final rawObjects = json['objects'] as List<dynamic>? ?? [];
    final objects = rawObjects
        .whereType<Map<String, dynamic>>()
        .map(DetectedObject.fromJson)
        .toList();

    return PerceptionResult(
      frameId: json['frame_id']?.toString() ?? '',
      timestampMs: (json['timestamp_ms'] as num?)?.toInt() ?? 0,
      source: json['source']?.toString() ?? '',
      objects: objects,
      sceneLabel: json['scene_label']?.toString() ?? 'general',
      sceneDescription: json['scene_description']?.toString(),
      hazards: (json['hazards'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      uncertainties: (json['uncertainties'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'frame_id': frameId,
        'timestamp_ms': timestampMs,
        'source': source,
        'objects': objects.map((e) => e.toJson()).toList(),
        'scene_label': sceneLabel,
        if (sceneDescription != null) 'scene_description': sceneDescription,
        'hazards': hazards,
        'uncertainties': uncertainties,
      };
}
