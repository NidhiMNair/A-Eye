/// Priority levels for assistive guidance.
enum PriorityLevel {
  low,
  medium,
  high,
  unknown;

  static PriorityLevel fromString(String? value) {
    if (value == null) return PriorityLevel.unknown;
    switch (value.trim().toLowerCase()) {
      case 'low':
        return PriorityLevel.low;
      case 'medium':
        return PriorityLevel.medium;
      case 'high':
        return PriorityLevel.high;
      default:
        return PriorityLevel.unknown;
    }
  }

  int get rank {
    switch (this) {
      case PriorityLevel.high:
        return 3;
      case PriorityLevel.medium:
        return 2;
      case PriorityLevel.low:
        return 1;
      case PriorityLevel.unknown:
        return 0;
    }
  }
}
