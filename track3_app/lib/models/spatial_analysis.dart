/// Image-space spatial interpretation of a detected object.
class SpatialObjectInfo {
  final String label;
  final double conf;
  final String horizontalZone;
  final String verticalZone;
  final bool isCentral;
  final bool isProminent;
  final List<String> relativePositions;

  const SpatialObjectInfo({
    required this.label,
    required this.conf,
    required this.horizontalZone,
    required this.verticalZone,
    required this.isCentral,
    required this.isProminent,
    required this.relativePositions,
  });

  factory SpatialObjectInfo.fromJson(Map<String, dynamic> json) {
    return SpatialObjectInfo(
      label: json['label']?.toString() ?? '',
      conf: (json['conf'] as num?)?.toDouble() ?? 0.0,
      horizontalZone: json['horizontal_zone']?.toString() ?? 'center',
      verticalZone: json['vertical_zone']?.toString() ?? 'middle',
      isCentral: json['is_central'] == true,
      isProminent: json['is_prominent'] == true,
      relativePositions: (json['relative_positions'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'label': label,
        'conf': conf,
        'horizontal_zone': horizontalZone,
        'vertical_zone': verticalZone,
        'is_central': isCentral,
        'is_prominent': isProminent,
        'relative_positions': relativePositions,
      };
}

/// Result of deterministic image-space spatial reasoning.
class SpatialAnalysis {
  final String frameId;
  final List<SpatialObjectInfo> objects;
  final List<SpatialObjectInfo> centralObjects;
  final List<SpatialObjectInfo> prominentObjects;
  final String sceneLabel;
  final String? sceneDescription;

  const SpatialAnalysis({
    required this.frameId,
    required this.objects,
    required this.centralObjects,
    required this.prominentObjects,
    required this.sceneLabel,
    this.sceneDescription,
  });

  factory SpatialAnalysis.fromJson(Map<String, dynamic> json) {
    List<SpatialObjectInfo> parseList(String key) {
      final list = json[key] as List<dynamic>? ?? [];
      return list.whereType<Map<String, dynamic>>().map(SpatialObjectInfo.fromJson).toList();
    }

    return SpatialAnalysis(
      frameId: json['frame_id']?.toString() ?? '',
      objects: parseList('objects'),
      centralObjects: parseList('central_objects'),
      prominentObjects: parseList('prominent_objects'),
      sceneLabel: json['scene_label']?.toString() ?? 'general',
      sceneDescription: json['scene_description']?.toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'frame_id': frameId,
        'objects': objects.map((e) => e.toJson()).toList(),
        'central_objects': centralObjects.map((e) => e.toJson()).toList(),
        'prominent_objects': prominentObjects.map((e) => e.toJson()).toList(),
        'scene_label': sceneLabel,
        if (sceneDescription != null) 'scene_description': sceneDescription,
      };
}
