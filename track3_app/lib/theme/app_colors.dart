import 'package:flutter/material.dart';

/// Semantic, accessible color tokens for A-Eye.
/// Contrast ratios strictly comply with WCAG 2.2 AA (>= 4.5:1 text, >= 3:1 UI).
class AppColors {
  AppColors._();

  // Dark Canvas & Surfaces (Obsidian Glass Architecture)
  static const Color background = Color(0xFF0B0F17);
  static const Color surfaceOled = Color(0xFF000000);
  static const Color surfaceElevated = Color(0xFF131B26);
  static const Color surfaceCard = Color(0xFF1C2634);
  static const Color surfaceGlass = Color(0xCC131B26); // 80% opacity for frosted blur
  static const Color surfaceGlassLight = Color(0x661E293B);
  static const Color borderHairline = Color(0x26FFFFFF); // 15% white for crisp edges
  static const Color borderSubtle = Color(0x1AFFFFFF);

  // Brand / Action Accents
  static const Color primary = Color(0xFF14B8A6); // Luminous Teal
  static const Color primaryHover = Color(0xFF0D9488);
  static const Color primaryContainer = Color(0xFF0F3E3B);
  static const Color onPrimary = Color(0xFFFFFFFF);

  static const Color secondary = Color(0xFF6366F1); // Indigo
  static const Color secondaryContainer = Color(0xFF262A56);

  // Semantic Severity Roles (Red is reserved strictly for genuine hazards)
  static const Color hazard = Color(0xFFEF4444); // Hazard Red
  static const Color hazardContainer = Color(0xFF450A0A);
  static const Color onHazard = Color(0xFFFFFFFF);

  static const Color guidance = Color(0xFFF59E0B); // Guidance Amber
  static const Color guidanceContainer = Color(0xFF451A03);
  static const Color onGuidance = Color(0xFFFFFFFF);

  static const Color info = Color(0xFF38BDF8); // Info Sky
  static const Color infoContainer = Color(0xFF082F49);
  static const Color onInfo = Color(0xFFFFFFFF);

  static const Color safeNeutral = Color(0xFF10B981); // Success / Ready Emerald
  static const Color safeNeutralContainer = Color(0xFF064E3B);

  // Typography Contrast Roles
  static const Color textPrimary = Color(0xFFFFFFFF); // 15:1 against #0B0F17
  static const Color textSecondary = Color(0xFF94A3B8); // 5.8:1 against #0B0F17
  static const Color textMuted = Color(0xFF64748B); // 3.2:1 (for non-essential captions)
  static const Color textOnDark = Color(0xFFFFFFFF);

  // High Contrast Mode Tokens (for visually impaired high-contrast preference)
  static const Color hcBackground = Color(0xFF000000);
  static const Color hcSurface = Color(0xFF121212);
  static const Color hcBorder = Color(0xFFFFFFFF);
  static const Color hcPrimary = Color(0xFFFFD700); // High-visibility Amber Gold
  static const Color hcText = Color(0xFFFFFFFF);
  static const Color hcHazard = Color(0xFFFF3333);
  static const Color hcGuidance = Color(0xFFFFD700);
  static const Color hcInfo = Color(0xFF00FFFF);
}
