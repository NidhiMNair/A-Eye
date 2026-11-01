/// Presentation-only text normalizer for UI display.
///
/// Cleans up visual anomalies produced by backend vision language models
/// (e.g. stray punctuation like ".,", double commas, unbalanced whitespace),
/// while preserving the exact semantic meaning of Track 2 decisions.
/// This formatter is strictly for screen display; the audio/TTS layer speaks the original string.
class DisplayTextFormatter {
  DisplayTextFormatter._();

  /// Clean and format guidance message for optimal screen legibility.
  static String formatGuidance(String raw) {
    if (raw.trim().isEmpty) return '';

    var text = raw.trim();

    // 1. Collapse stray adjacent punctuation (e.g. ".,", "..", ",,", ".:")
    text = text.replaceAll(RegExp(r'\s*\.\s*,'), ',');
    text = text.replaceAll(RegExp(r'\s*,\s*\.'), '.');
    text = text.replaceAll(RegExp(r'\.{2,}'), '.');
    text = text.replaceAll(RegExp(r',{2,}'), ',');
    text = text.replaceAll(RegExp(r':{2,}'), ':');

    // 2. Normalize whitespace around punctuation
    text = text.replaceAllMapped(RegExp(r'\s+([,.:;!?])'), (m) => m[1]!);
    text = text.replaceAllMapped(RegExp(r'([,.:;!?])(?=[^\s\d])'), (m) => '${m[1]} ');
    text = text.replaceAll(RegExp(r'\s{2,}'), ' ');

    // 3. Ensure sentence starts with capital letter and capitalize after sentence terminators
    text = text.replaceAllMapped(
      RegExp(r'(^|[.!?]\s+)([a-z])'),
      (m) => '${m[1]}${m[2]!.toUpperCase()}',
    );

    // 4. Clean trailing comma or colon
    text = text.replaceAll(RegExp(r'[,:\s]+$'), '');

    return text.trim();
  }

  /// Format human-friendly, glanceable system status titles.
  /// Eliminates developer jargon ("Inference complete: ALERT" -> "Hazard Detected").
  static String formatStatusTitle({
    required bool isSpeaking,
    required bool isInferring,
    required bool hasError,
    required bool isOnline,
    required String? categoryDisplay,
  }) {
    if (!isOnline) return 'Server Offline';
    if (hasError) return 'Connection Interrupted';
    if (isSpeaking) return 'Speaking Guidance';
    if (isInferring) return 'Analyzing Scene';

    final cat = (categoryDisplay ?? '').toLowerCase();
    if (cat.contains('alert')) return 'Hazard Ahead';
    if (cat.contains('guidance')) return 'Path Guidance';
    if (cat.contains('info')) return 'Environment Note';

    return 'Ready & Scanning';
  }
}
