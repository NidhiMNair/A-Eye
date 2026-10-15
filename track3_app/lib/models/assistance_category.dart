/// Actionable assistance category produced by Track 2.
enum AssistanceCategory {
  alert,
  guidance,
  info,
  none,
  unknown;

  static AssistanceCategory fromString(String? value) {
    if (value == null) return AssistanceCategory.unknown;
    switch (value.trim().toLowerCase()) {
      case 'alert':
        return AssistanceCategory.alert;
      case 'guidance':
        return AssistanceCategory.guidance;
      case 'info':
        return AssistanceCategory.info;
      case 'none':
        return AssistanceCategory.none;
      default:
        return AssistanceCategory.unknown;
    }
  }

  String toDisplayString() {
    switch (this) {
      case AssistanceCategory.alert:
        return 'ALERT';
      case AssistanceCategory.guidance:
        return 'GUIDANCE';
      case AssistanceCategory.info:
        return 'INFO';
      case AssistanceCategory.none:
        return 'NONE';
      case AssistanceCategory.unknown:
        return 'UNKNOWN';
    }
  }
}
