import 'priority_level.dart';

/// An observation rated for user navigation relevance.
class PrioritizedItem {
  final String item;
  final PriorityLevel priority;
  final String reason;
  final bool isHazard;

  const PrioritizedItem({
    required this.item,
    required this.priority,
    required this.reason,
    this.isHazard = false,
  });

  factory PrioritizedItem.fromJson(Map<String, dynamic> json) {
    return PrioritizedItem(
      item: json['item']?.toString() ?? '',
      priority: PriorityLevel.fromString(json['priority']?.toString()),
      reason: json['reason']?.toString() ?? '',
      isHazard: json['is_hazard'] == true,
    );
  }

  Map<String, dynamic> toJson() => {
        'item': item,
        'priority': priority.name,
        'reason': reason,
        'is_hazard': isHazard,
      };
}
