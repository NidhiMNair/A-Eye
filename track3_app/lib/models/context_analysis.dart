/// Temporal and multi-frame context reasoning output.
class ContextAnalysis {
  final bool isMultiFrame;
  final int frameCount;
  final List<String> persistentObjects;
  final List<String> newObjects;
  final List<String> centralPersistence;
  final List<String> repeatedHazards;
  final List<String> changes;

  const ContextAnalysis({
    this.isMultiFrame = false,
    this.frameCount = 1,
    this.persistentObjects = const [],
    this.newObjects = const [],
    this.centralPersistence = const [],
    this.repeatedHazards = const [],
    this.changes = const [],
  });

  factory ContextAnalysis.fromJson(Map<String, dynamic> json) {
    List<String> parseStrings(String key) {
      final list = json[key] as List<dynamic>? ?? [];
      return list.map((e) => e.toString()).toList();
    }

    return ContextAnalysis(
      isMultiFrame: json['is_multi_frame'] == true,
      frameCount: (json['frame_count'] as num?)?.toInt() ?? 1,
      persistentObjects: parseStrings('persistent_objects'),
      newObjects: parseStrings('new_objects'),
      centralPersistence: parseStrings('central_persistence'),
      repeatedHazards: parseStrings('repeated_hazards'),
      changes: parseStrings('changes'),
    );
  }

  Map<String, dynamic> toJson() => {
        'is_multi_frame': isMultiFrame,
        'frame_count': frameCount,
        'persistent_objects': persistentObjects,
        'new_objects': newObjects,
        'central_persistence': centralPersistence,
        'repeated_hazards': repeatedHazards,
        'changes': changes,
      };
}
