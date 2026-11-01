import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_spacing.dart';
import 'app_typography.dart';

/// ThemeExtension providing semantic tokens across the component kit.
class AEyeTokens extends ThemeExtension<AEyeTokens> {
  final Color bgCanvas;
  final Color surfaceGlass;
  final Color surfaceCard;
  final Color borderSubtle;
  final Color brandPrimary;
  final Color hazardColor;
  final Color guidanceColor;
  final Color infoColor;
  final Color textMain;
  final Color textMuted;
  final bool isHighContrast;

  const AEyeTokens({
    required this.bgCanvas,
    required this.surfaceGlass,
    required this.surfaceCard,
    required this.borderSubtle,
    required this.brandPrimary,
    required this.hazardColor,
    required this.guidanceColor,
    required this.infoColor,
    required this.textMain,
    required this.textMuted,
    this.isHighContrast = false,
  });

  static const standardDark = AEyeTokens(
    bgCanvas: AppColors.background,
    surfaceGlass: AppColors.surfaceGlass,
    surfaceCard: AppColors.surfaceCard,
    borderSubtle: AppColors.borderHairline,
    brandPrimary: AppColors.primary,
    hazardColor: AppColors.hazard,
    guidanceColor: AppColors.guidance,
    infoColor: AppColors.info,
    textMain: AppColors.textPrimary,
    textMuted: AppColors.textSecondary,
    isHighContrast: false,
  );

  static const highContrast = AEyeTokens(
    bgCanvas: AppColors.hcBackground,
    surfaceGlass: AppColors.hcSurface,
    surfaceCard: AppColors.hcSurface,
    borderSubtle: AppColors.hcBorder,
    brandPrimary: AppColors.hcPrimary,
    hazardColor: AppColors.hcHazard,
    guidanceColor: AppColors.hcGuidance,
    infoColor: AppColors.hcInfo,
    textMain: AppColors.hcText,
    textMuted: AppColors.hcText,
    isHighContrast: true,
  );

  @override
  AEyeTokens copyWith({
    Color? bgCanvas,
    Color? surfaceGlass,
    Color? surfaceCard,
    Color? borderSubtle,
    Color? brandPrimary,
    Color? hazardColor,
    Color? guidanceColor,
    Color? infoColor,
    Color? textMain,
    Color? textMuted,
    bool? isHighContrast,
  }) {
    return AEyeTokens(
      bgCanvas: bgCanvas ?? this.bgCanvas,
      surfaceGlass: surfaceGlass ?? this.surfaceGlass,
      surfaceCard: surfaceCard ?? this.surfaceCard,
      borderSubtle: borderSubtle ?? this.borderSubtle,
      brandPrimary: brandPrimary ?? this.brandPrimary,
      hazardColor: hazardColor ?? this.hazardColor,
      guidanceColor: guidanceColor ?? this.guidanceColor,
      infoColor: infoColor ?? this.infoColor,
      textMain: textMain ?? this.textMain,
      textMuted: textMuted ?? this.textMuted,
      isHighContrast: isHighContrast ?? this.isHighContrast,
    );
  }

  @override
  AEyeTokens lerp(ThemeExtension<AEyeTokens>? other, double t) {
    if (other is! AEyeTokens) return this;
    return AEyeTokens(
      bgCanvas: Color.lerp(bgCanvas, other.bgCanvas, t) ?? bgCanvas,
      surfaceGlass: Color.lerp(surfaceGlass, other.surfaceGlass, t) ?? surfaceGlass,
      surfaceCard: Color.lerp(surfaceCard, other.surfaceCard, t) ?? surfaceCard,
      borderSubtle: Color.lerp(borderSubtle, other.borderSubtle, t) ?? borderSubtle,
      brandPrimary: Color.lerp(brandPrimary, other.brandPrimary, t) ?? brandPrimary,
      hazardColor: Color.lerp(hazardColor, other.hazardColor, t) ?? hazardColor,
      guidanceColor: Color.lerp(guidanceColor, other.guidanceColor, t) ?? guidanceColor,
      infoColor: Color.lerp(infoColor, other.infoColor, t) ?? infoColor,
      textMain: Color.lerp(textMain, other.textMain, t) ?? textMain,
      textMuted: Color.lerp(textMuted, other.textMuted, t) ?? textMuted,
      isHighContrast: t > 0.5 ? other.isHighContrast : isHighContrast,
    );
  }
}

/// Factory for building cohesive Material 3 ThemeData with our design tokens.
class AppTheme {
  AppTheme._();

  static ThemeData buildTheme({bool highContrast = false}) {
    final tokens = highContrast ? AEyeTokens.highContrast : AEyeTokens.standardDark;

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: tokens.bgCanvas,
      primaryColor: tokens.brandPrimary,
      fontFamily: AppTypography.bodyFontFamily,
      colorScheme: ColorScheme(
        brightness: Brightness.dark,
        primary: tokens.brandPrimary,
        onPrimary: AppColors.onPrimary,
        secondary: AppColors.secondary,
        onSecondary: Colors.white,
        error: tokens.hazardColor,
        onError: Colors.white,
        surface: tokens.surfaceCard,
        onSurface: tokens.textMain,
        surfaceContainerHighest: tokens.surfaceGlass,
        outline: tokens.borderSubtle,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: AppTypography.headlineMedium.copyWith(color: tokens.textMain),
        iconTheme: IconThemeData(color: tokens.textMain, size: 24),
      ),
      cardTheme: CardThemeData(
        color: tokens.surfaceCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: AppSpacing.roundedLg,
          side: BorderSide(color: tokens.borderSubtle, width: 1),
        ),
      ),
      extensions: [tokens],
    );
  }
}

extension AEyeThemeContext on BuildContext {
  AEyeTokens get tokens => Theme.of(this).extension<AEyeTokens>() ?? AEyeTokens.standardDark;
}
