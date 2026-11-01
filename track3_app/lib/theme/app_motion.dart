import 'package:flutter/material.dart';

/// Motion and choreography tokens for A-Eye.
/// Emulates Google Material 3 Expressive spring physics.
/// Respects MediaQuery.disableAnimations / prefers-reduced-motion.
class AppMotion {
  AppMotion._();

  // Durations
  static const Duration micro = Duration(milliseconds: 120);
  static const Duration quick = Duration(milliseconds: 200);
  static const Duration standard = Duration(milliseconds: 300);
  static const Duration emphasize = Duration(milliseconds: 450);
  static const Duration auraBreathing = Duration(milliseconds: 2200);

  // Easing Curves
  static const Curve expressiveOut = Cubic(0.16, 1.0, 0.3, 1.0);
  static const Curve standardDecelerate = Cubic(0.05, 0.7, 0.1, 1.0);
  static const Curve standardAccelerate = Cubic(0.3, 0.0, 0.8, 0.15);
  static const Curve springy = Curves.easeOutBack;

  /// Helper to get effective duration honoring reduced-motion accessibility setting.
  static Duration getDuration(BuildContext context, Duration original) {
    if (MediaQuery.of(context).disableAnimations) {
      return Duration.zero;
    }
    return original;
  }
}
