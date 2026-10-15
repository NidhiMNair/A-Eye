import 'assistance_category.dart';
import 'prioritized_item.dart';
import 'priority_level.dart';

/// Structured assistance recommendation produced by Track 2.
class AssistanceDecision {
  final AssistanceCategory category;
  final PriorityLevel priority;
  final String message;
  final List<PrioritizedItem> relevantItems;

  const AssistanceDecision({
    required this.category,
    required this.priority,
    required this.message,
    required this.relevantItems,
  });

  factory AssistanceDecision.fromJson(Map<String, dynamic> json) {
    final rawItems = json['relevant_items'] as List<dynamic>? ?? [];
    final items = rawItems
        .whereType<Map<String, dynamic>>()
        .map(PrioritizedItem.fromJson)
        .toList();

    return AssistanceDecision(
      category: AssistanceCategory.fromString(json['category']?.toString()),
      priority: PriorityLevel.fromString(json['priority']?.toString()),
      message: json['message']?.toString() ?? '',
      relevantItems: items,
    );
  }

  Map<String, dynamic> toJson() => {
        'category': category.name,
        'priority': priority.name,
        'message': message,
        'relevant_items': relevantItems.map((e) => e.toJson()).toList(),
      };
}
