/// Normalized 2D bounding box in image coordinates [0.0, 1.0].
class BoundingBox {
  final double xMin;
  final double yMin;
  final double xMax;
  final double yMax;

  const BoundingBox({
    required this.xMin,
    required this.yMin,
    required this.xMax,
    required this.yMax,
  });

  factory BoundingBox.fromJson(Map<String, dynamic> json) {
    return BoundingBox(
      xMin: (json['x_min'] as num?)?.toDouble() ?? 0.0,
      yMin: (json['y_min'] as num?)?.toDouble() ?? 0.0,
      xMax: (json['x_max'] as num?)?.toDouble() ?? 1.0,
      yMax: (json['y_max'] as num?)?.toDouble() ?? 1.0,
    );
  }

  Map<String, dynamic> toJson() => {
        'x_min': xMin,
        'y_min': yMin,
        'x_max': xMax,
        'y_max': yMax,
      };
}
