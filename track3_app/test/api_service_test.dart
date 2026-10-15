import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:track3_app/config/app_config.dart';
import 'package:track3_app/services/track2_api_service.dart';

void main() {
  group('10: Track2ApiService Error Handling', () {
    test('400 bad request throws structured Track2ApiException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': {
              'error_code': 'NO_FRAMES_PROVIDED',
              'message': 'No image frames received.',
            }
          }),
          400,
          headers: {'content-type': 'application/json'},
        );
      });

      final config = AppConfig(backendBaseUrl: 'http://localhost:5000');
      final service = Track2ApiService(config: config, client: mockClient);

      expect(
        () => service.processFrames(frameBytesList: [Uint8List.fromList([1, 2, 3])]),
        throwsA(isA<Track2ApiException>().having(
          (e) => e.errorCode,
          'errorCode',
          'NO_FRAMES_PROVIDED',
        )),
      );
    });

    test('502 VLM error throws typed Track2VlmException', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({
            'detail': {
              'error_code': 'VLM_ERROR',
              'message': 'Gemini quota exceeded',
            }
          }),
          502,
          headers: {'content-type': 'application/json'},
        );
      });

      final config = AppConfig(backendBaseUrl: 'http://localhost:5000');
      final service = Track2ApiService(config: config, client: mockClient);

      expect(
        () => service.processFrames(frameBytesList: [Uint8List.fromList([1, 2, 3])]),
        throwsA(isA<Track2VlmException>().having(
          (e) => e.message,
          'message',
          'Gemini quota exceeded',
        )),
      );
    });

    test('Network client failure throws Track2NetworkException', () async {
      final mockClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final config = AppConfig(backendBaseUrl: 'http://localhost:5000');
      final service = Track2ApiService(config: config, client: mockClient);

      expect(
        () => service.checkHealth(),
        throwsA(isA<Track2NetworkException>()),
      );
    });
  });
}
