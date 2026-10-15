import 'package:flutter_test/flutter_test.dart';
import 'package:track3_app/models/models.dart';

void main() {
  group('1, 2, 3: Models, Categories & Priority Parsing', () {
    test('Track2Result JSON parsing maps all fields accurately', () {
      final json = {
        'frame_id': 'frame_test_101',
        'timestamp_ms': 1700000000000,
        'decision': {
          'category': 'alert',
          'priority': 'high',
          'message': 'Obstacle or hazard detected in path: chair',
          'relevant_items': [
            {
              'item': 'chair',
              'priority': 'high',
              'reason': 'Directly in central walkway',
              'is_hazard': true,
            }
          ]
        },
        'perception': {
          'frame_id': 'frame_test_101',
          'timestamp_ms': 1700000000000,
          'source': 'offline_mock',
          'objects': [
            {
              'label': 'chair',
              'conf': 0.95,
              'bbox': {
                'x_min': 0.3,
                'y_min': 0.4,
                'x_max': 0.7,
                'y_max': 0.9,
              },
            }
          ],
          'scene_label': 'indoor_corridor',
          'scene_description': 'Hallway with a central chair',
          'hazards': ['chair in center'],
          'uncertainties': [],
        },
        'spatial': {
          'frame_id': 'frame_test_101',
          'objects': [
            {
              'label': 'chair',
              'conf': 0.95,
              'horizontal_zone': 'center',
              'vertical_zone': 'middle',
              'is_central': true,
              'is_prominent': true,
              'relative_positions': [],
            }
          ],
          'central_objects': [],
          'prominent_objects': [],
          'scene_label': 'indoor_corridor',
        },
        'context': {
          'is_multi_frame': false,
          'frame_count': 1,
          'persistent_objects': [],
          'new_objects': ['chair'],
          'central_persistence': [],
          'repeated_hazards': [],
          'changes': ['Baseline observation established.'],
        },
        'summary': '[ALERT] Priority: high. Obstacle or hazard detected in path: chair',
      };

      final result = Track2Result.fromJson(json);

      expect(result.frameId, 'frame_test_101');
      expect(result.timestampMs, 1700000000000);
      expect(result.decision.category, AssistanceCategory.alert);
      expect(result.decision.priority, PriorityLevel.high);
      expect(result.decision.message, 'Obstacle or hazard detected in path: chair');
      expect(result.decision.relevantItems.length, 1);
      expect(result.decision.relevantItems.first.item, 'chair');
      expect(result.decision.relevantItems.first.isHazard, isTrue);
      expect(result.perception.objects.first.label, 'chair');
      expect(result.perception.objects.first.bbox.xMin, 0.3);
      expect(result.spatial.objects.first.isCentral, isTrue);
      expect(result.context.newObjects, contains('chair'));
    });

    test('AssistanceCategory parses all enum values and unknown fallback', () {
      expect(AssistanceCategory.fromString('alert'), AssistanceCategory.alert);
      expect(AssistanceCategory.fromString('ALERT'), AssistanceCategory.alert);
      expect(AssistanceCategory.fromString('guidance'), AssistanceCategory.guidance);
      expect(AssistanceCategory.fromString('info'), AssistanceCategory.info);
      expect(AssistanceCategory.fromString('none'), AssistanceCategory.none);
      expect(AssistanceCategory.fromString('invalid_xyz'), AssistanceCategory.unknown);
      expect(AssistanceCategory.fromString(null), AssistanceCategory.unknown);
    });

    test('PriorityLevel parses all enum values and rank comparisons', () {
      expect(PriorityLevel.fromString('high'), PriorityLevel.high);
      expect(PriorityLevel.fromString('HIGH'), PriorityLevel.high);
      expect(PriorityLevel.fromString('medium'), PriorityLevel.medium);
      expect(PriorityLevel.fromString('low'), PriorityLevel.low);
      expect(PriorityLevel.fromString('unknown_val'), PriorityLevel.unknown);
      expect(PriorityLevel.fromString(null), PriorityLevel.unknown);

      expect(PriorityLevel.high.rank, greaterThan(PriorityLevel.medium.rank));
      expect(PriorityLevel.medium.rank, greaterThan(PriorityLevel.low.rank));
      expect(PriorityLevel.low.rank, greaterThan(PriorityLevel.unknown.rank));
    });
  });
}
