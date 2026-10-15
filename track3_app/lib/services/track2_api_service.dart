import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/models.dart';

/// Base exception for Track 2 API operations.
class Track2ApiException implements Exception {
  final String message;
  final String? errorCode;
  final int? statusCode;

  const Track2ApiException(this.message, {this.errorCode, this.statusCode});

  @override
  String toString() => 'Track2ApiException: $message (code=$errorCode, status=$statusCode)';
}

/// Thrown when the backend cannot be reached.
class Track2NetworkException extends Track2ApiException {
  const Track2NetworkException(super.message, {super.statusCode});
}

/// Thrown when VLM processing fails on the backend.
class Track2VlmException extends Track2ApiException {
  const Track2VlmException(super.message, {super.errorCode, super.statusCode});
}

/// Health response returned by the Track 2 bridge.
class BridgeHealthStatus {
  final bool isHealthy;
  final String vlmMode;
  final bool track2Available;
  final String? warning;

  const BridgeHealthStatus({
    required this.isHealthy,
    required this.vlmMode,
    required this.track2Available,
    this.warning,
  });

  factory BridgeHealthStatus.fromJson(Map<String, dynamic> json) {
    return BridgeHealthStatus(
      isHealthy: json['status'] == 'healthy',
      vlmMode: json['vlm_mode']?.toString() ?? 'unknown',
      track2Available: json['track2_available'] == true,
      warning: json['init_warning']?.toString(),
    );
  }
}

/// Service managing HTTP communication with the Python Track 2 bridge.
class Track2ApiService {
  final AppConfig config;
  final http.Client _client;

  Track2ApiService({
    required this.config,
    http.Client? client,
  }) : _client = client ?? http.Client();

  /// Query the bridge health status.
  Future<BridgeHealthStatus> checkHealth({Duration timeout = const Duration(seconds: 4)}) async {
    final uri = Uri.parse('${config.backendBaseUrl}/health');
    try {
      final response = await _client.get(uri).timeout(timeout);
      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        return BridgeHealthStatus.fromJson(decoded);
      }
      throw Track2ApiException(
        'Health check returned status ${response.statusCode}',
        statusCode: response.statusCode,
      );
    } on TimeoutException {
      throw const Track2NetworkException('Health check timed out');
    } catch (e) {
      if (e is Track2ApiException) rethrow;
      throw Track2NetworkException('Could not connect to Track 2 backend: $e');
    }
  }

  /// Reset Track 2 temporal context history for a fresh session.
  Future<void> resetSession({Duration timeout = const Duration(seconds: 5)}) async {
    final uri = Uri.parse('${config.backendBaseUrl}/session/reset');
    try {
      final response = await _client.post(uri).timeout(timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw Track2ApiException(
          'Session reset failed: ${response.statusCode}',
          statusCode: response.statusCode,
        );
      }
    } on TimeoutException {
      throw const Track2NetworkException('Session reset request timed out');
    } catch (e) {
      if (e is Track2ApiException) rethrow;
      throw Track2NetworkException('Could not reach backend for session reset: $e');
    }
  }

  /// Upload one or more image frames for Track 2 reasoning.
  Future<Track2Result> processFrames({
    required List<Uint8List> frameBytesList,
    String? frameId,
    int? timestampMs,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    if (frameBytesList.isEmpty) {
      throw const Track2ApiException('Cannot process an empty list of frames', errorCode: 'EMPTY_FRAMES');
    }

    final uri = Uri.parse('${config.backendBaseUrl}/process-frames');
    final request = http.MultipartRequest('POST', uri);

    if (frameId != null) {
      request.fields['frame_id'] = frameId;
    }
    if (timestampMs != null) {
      request.fields['timestamp_ms'] = timestampMs.toString();
    }

    for (var i = 0; i < frameBytesList.length; i++) {
      final bytes = frameBytesList[i];
      request.files.add(
        http.MultipartFile.fromBytes(
          'files',
          bytes,
          filename: 'frame_$i.jpg',
        ),
      );
    }

    try {
      final streamedResponse = await _client.send(request).timeout(timeout);
      final response = await http.Response.fromStream(streamedResponse);

      Map<String, dynamic> bodyJson;
      try {
        bodyJson = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (e) {
        throw Track2ApiException(
          'Failed to decode backend response (status ${response.statusCode})',
          statusCode: response.statusCode,
        );
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return Track2Result.fromJson(bodyJson);
      }

      final detail = bodyJson['detail'];
      String message = 'Backend error: ${response.statusCode}';
      String? errorCode;

      if (detail is Map<String, dynamic>) {
        message = detail['message']?.toString() ?? message;
        errorCode = detail['error_code']?.toString();
      } else if (bodyJson['message'] != null) {
        message = bodyJson['message'].toString();
        errorCode = bodyJson['error_code']?.toString();
      }

      if (response.statusCode == 502 || errorCode == 'VLM_ERROR') {
        throw Track2VlmException(message, errorCode: errorCode, statusCode: response.statusCode);
      }

      throw Track2ApiException(message, errorCode: errorCode, statusCode: response.statusCode);
    } on TimeoutException {
      throw const Track2NetworkException('Frame processing timed out (backend took too long)');
    } catch (e) {
      if (e is Track2ApiException) rethrow;
      throw Track2NetworkException('Network error communicating with Track 2 backend: $e');
    }
  }

  void dispose() {
    _client.close();
  }
}
