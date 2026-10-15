import 'bounding_box.dart';

/// A detected object in image coordinates.
class DetectedObject {
  final String label;
  final double conf;
  final BoundingBox bbox;
  final int? trackId;

  const DetectedObject({
    required this.label,
    required this.conf,
    required this.bbox,
    this.trackId,
  });

  factory DetectedObject.fromJson(Map<String, dynamic> json) {
    return DetectedObject(
      label: json['label']?.toString() ?? '',
      conf: (json['conf'] as num?)?.toDouble() ?? 0.0,
      bbox: BoundingBox.fromJson(json['bbox'] as Map<String, dynamic>? ?? {}),
      trackId: json['track_id'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
        'label': label,
        'conf': conf,
        'bbox': bbox.toJson(),
        if (trackId != null) 'track_id': trackId,
      };
}
