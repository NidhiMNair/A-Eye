import 'package:flutter/material.dart';

/// Spacing, radii, and elevation geometry for A-Eye.
class AppSpacing {
  AppSpacing._();

  static const double xxs = 4.0;
  static const double xs = 8.0;
  static const double sm = 12.0;
  static const double md = 16.0;
  static const double lg = 20.0;
  static const double xl = 24.0;
  static const double xxl = 32.0;
  static const double huge = 48.0;

  // Touch Target Minimums
  static const double minTouchTarget = 48.0;
  static const double primaryActionHeight = 92.0;

  // Radii
  static const Radius radiusSm = Radius.circular(8.0);
  static const Radius radiusMd = Radius.circular(14.0);
  static const Radius radiusLg = Radius.circular(20.0);
  static const Radius radiusXl = Radius.circular(28.0);
  static const Radius radiusPill = Radius.circular(999.0);

  static final BorderRadius roundedSm = BorderRadius.circular(8.0);
  static final BorderRadius roundedMd = BorderRadius.circular(14.0);
  static final BorderRadius roundedLg = BorderRadius.circular(20.0);
  static final BorderRadius roundedXl = BorderRadius.circular(28.0);
  static final BorderRadius roundedPill = BorderRadius.circular(999.0);

  // Blur strengths
  static const double glassBlurSigma = 16.0;
  static const double subtleBlurSigma = 8.0;
}
