import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../config/app_config.dart';

/// Service managing Text-To-Speech audio output.
class SpeechService {
  FlutterTts? _tts;
  final AppConfig config;

  bool _isSpeaking = false;
  bool _isInitialized = false;

  final StreamController<bool> _speakingStateController = StreamController<bool>.broadcast();

  SpeechService({
    required this.config,
    FlutterTts? initialTts,
  }) : _tts = initialTts;

  FlutterTts get _ttsInstance => _tts ??= FlutterTts();

  bool get isSpeaking => _isSpeaking;
  Stream<bool> get speakingStateStream => _speakingStateController.stream;

  /// Configure TTS voice engine, language, and event handlers.
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // Attempt preferred Indian English voice; fallback to en-US if unavailable
      final languages = await _ttsInstance.getLanguages;
      final langList = (languages as List<dynamic>? ?? []).map((e) => e.toString().toLowerCase()).toList();

      if (langList.any((l) => l.contains('en-in') || l.contains('en_in'))) {
        await _ttsInstance.setLanguage('en-IN');
      } else {
        await _ttsInstance.setLanguage('en-US');
      }

      await _ttsInstance.awaitSpeakCompletion(true);
      await _ttsInstance.setSpeechRate(config.ttsSpeechRate);
      await _ttsInstance.setVolume(1.0);
      await _ttsInstance.setPitch(1.0);

      _ttsInstance.setStartHandler(() {
        _isSpeaking = true;
        if (!_speakingStateController.isClosed) {
          _speakingStateController.add(true);
        }
      });

      _ttsInstance.setCompletionHandler(() {
        _isSpeaking = false;
        if (!_speakingStateController.isClosed) {
          _speakingStateController.add(false);
        }
      });

      _ttsInstance.setCancelHandler(() {
        _isSpeaking = false;
        if (!_speakingStateController.isClosed) {
          _speakingStateController.add(false);
        }
      });

      _ttsInstance.setErrorHandler((dynamic msg) {
        _isSpeaking = false;
        if (!_speakingStateController.isClosed) {
          _speakingStateController.add(false);
        }
        debugPrint('SpeechService error: $msg');
      });

      _isInitialized = true;
    } catch (e) {
      debugPrint('SpeechService initialization failed: $e');
    }
  }

  /// Speak a message.
  /// If [interrupt] is true, immediately halts any active speech and begins speaking.
  Future<void> speak(String text, {bool interrupt = false}) async {
    final cleanText = text.trim();
    if (cleanText.isEmpty) return;

    if (!_isInitialized) {
      await initialize();
    }

    try {
      // If speech is currently ongoing and interruption is NOT requested, let current sentence finish
      if (_isSpeaking && !interrupt) {
        return;
      }

      if (interrupt && _isSpeaking) {
        await _ttsInstance.stop();
      }

      _isSpeaking = true;
      if (!_speakingStateController.isClosed) {
        _speakingStateController.add(true);
      }

      await _ttsInstance.setSpeechRate(config.ttsSpeechRate);
      await _ttsInstance.speak(cleanText);
    } catch (e) {
      _isSpeaking = false;
      if (!_speakingStateController.isClosed) {
        _speakingStateController.add(false);
      }
      debugPrint('SpeechService: speak error: $e');
    }
  }

  /// Stop any active speech playback.
  Future<void> stop() async {
    try {
      await _ttsInstance.stop();
      _isSpeaking = false;
      if (!_speakingStateController.isClosed) {
        _speakingStateController.add(false);
      }
    } catch (e) {
      debugPrint('SpeechService: stop error: $e');
    }
  }

  void dispose() {
    stop();
    _speakingStateController.close();
  }
}
