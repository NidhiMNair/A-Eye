"""
track2/decision.py
====================
Deterministic priority/risk reasoning and assistance decision engine.

Evaluates observations into conservative priority levels (LOW, MEDIUM, HIGH)
and produces a structured AssistanceDecision for Track 3.

CONSTRAINTS:
  - Does NOT generate spoken sentences or TTS audio.
  - Does NOT command physical user actions ("walk left", "cross road").
  - Does NOT claim areas are safe to approach.
  - Keeps priority evaluation conservative and evidence-based.
"""

from __future__ import annotations

from track2.models import (
    AssistanceCategory,
    AssistanceDecision,
    ContextAnalysis,
    PerceptionResult,
    PrioritizedItem,
    PriorityLevel,
    SpatialAnalysis,
    VerticalZone,
)


class AssistanceDecisionEngine:
    """
    Deterministic priority scoring and assistance decision engine.
    """

    def decide(
        self,
        perception: PerceptionResult,
        spatial: SpatialAnalysis,
        context: ContextAnalysis,
    ) -> AssistanceDecision:
        """
        Evaluate perception, spatial, and context data into a structured decision.

        Args:
            perception: VLM perception observations.
            spatial: Image-space spatial analysis.
            context: Context and temporal persistence analysis.

        Returns:
            AssistanceDecision containing category, priority, concise summary
            message, and prioritized items.
        """
        prioritized_items: list[PrioritizedItem] = []

        # 1. Evaluate explicit hazards from VLM
        for hazard in perception.hazards:
            is_repeated = hazard in context.repeated_hazards
            priority = PriorityLevel.HIGH if is_repeated or spatial.central_objects else PriorityLevel.HIGH
            prioritized_items.append(
                PrioritizedItem(
                    item=hazard,
                    priority=priority,
                    reason="Visually supported obstacle or traversal hazard",
                    is_hazard=True,
                )
            )

        # 2. Evaluate central camera view objects (potential obstacles in path)
        for obj in spatial.central_objects:
            # Objects in middle/lower central view or prominent objects represent path obstacles
            is_path_obstacle = (
                obj.vertical_zone in (VerticalZone.MIDDLE, VerticalZone.LOWER)
                or obj.is_prominent
            )
            priority = PriorityLevel.HIGH if is_path_obstacle else PriorityLevel.MEDIUM
            reason = (
                f"Object '{obj.label}' is directly in the central camera view"
                if is_path_obstacle
                else f"Object '{obj.label}' is visible in central corridor"
            )
            prioritized_items.append(
                PrioritizedItem(
                    item=obj.label,
                    priority=priority,
                    reason=reason,
                    is_hazard=is_path_obstacle,
                )
            )

        # 3. Evaluate non-central prominent objects
        for obj in spatial.prominent_objects:
            if obj not in spatial.central_objects:
                prioritized_items.append(
                    PrioritizedItem(
                        item=obj.label,
                        priority=PriorityLevel.MEDIUM,
                        reason=f"Prominent object '{obj.label}' located on {obj.horizontal_zone.value}",
                        is_hazard=False,
                    )
                )

        # 4. Evaluate peripheral and background objects
        for obj in spatial.objects:
            if obj not in spatial.central_objects and obj not in spatial.prominent_objects:
                prioritized_items.append(
                    PrioritizedItem(
                        item=obj.label,
                        priority=PriorityLevel.LOW,
                        reason=f"Peripheral object '{obj.label}' located on {obj.horizontal_zone.value}",
                        is_hazard=False,
                    )
                )

        # Determine overall category and top priority
        has_high = any(item.priority == PriorityLevel.HIGH for item in prioritized_items)
        has_med = any(item.priority == PriorityLevel.MEDIUM for item in prioritized_items)

        if has_high:
            category = AssistanceCategory.ALERT
            overall_priority = PriorityLevel.HIGH
            high_items = [i.item for i in prioritized_items if i.priority == PriorityLevel.HIGH]
            message = f"Obstacle or hazard detected in path: {', '.join(high_items)}"
        elif has_med:
            category = AssistanceCategory.GUIDANCE
            overall_priority = PriorityLevel.MEDIUM
            med_items = [i.item for i in prioritized_items if i.priority == PriorityLevel.MEDIUM]
            message = f"Relevant objects detected in field of view: {', '.join(med_items)}"
        elif prioritized_items or perception.scene_description:
            category = AssistanceCategory.INFO
            overall_priority = PriorityLevel.LOW
            message = f"Scene context: {perception.scene_label}"
        else:
            category = AssistanceCategory.NONE
            overall_priority = PriorityLevel.LOW
            message = "No actionable assistance information detected in current frame."

        return AssistanceDecision(
            category=category,
            priority=overall_priority,
            message=message,
            relevant_items=prioritized_items,
        )
