import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:image/image.dart' as img;

/// Service managing device camera lifecycle, hardware initialization,
/// preview feed, and periodic snapshot sampling.
class CameraService {
  CameraController? _controller;
  bool _isInitializing = false;
  bool _isCapturing = false;
  CameraDescription? _selectedCamera;

  CameraController? get controller => _controller;
  bool get isInitialized => _controller != null && _controller!.value.isInitialized;
  CameraDescription? get selectedCamera => _selectedCamera;

  /// Initialize the rear device camera.
  Future<void> initialize({
    ResolutionPreset resolution = ResolutionPreset.medium,
  }) async {
    if (isInitialized || _isInitializing) return;
    _isInitializing = true;

    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw Exception('No cameras found on this device');
      }

      // Prioritize the back/rear-facing camera for navigation perspective
      _selectedCamera = cameras.firstWhere(
        (cam) => cam.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      final controller = CameraController(
        _selectedCamera!,
        resolution,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await controller.initialize();
      _controller = controller;
    } finally {
      _isInitializing = false;
    }
  }

  /// Capture a single upright JPEG frame from the active camera.
  Future<Uint8List?> captureFrameJpeg({
    int quality = 75,
    int maxWidth = 720,
  }) async {
    final ctrl = _controller;
    if (ctrl == null || !ctrl.value.isInitialized || _isCapturing) {
      return null;
    }

    _isCapturing = true;
    try {
      final xFile = await ctrl.takePicture();
      final rawBytes = await xFile.readAsBytes();

      // If already within size limits, return raw hardware JPEG
      if (rawBytes.lengthInBytes < 150000 && maxWidth >= 1280) {
        return rawBytes;
      }

      // Decode and optimize/orient in compute isolate to avoid blocking UI
      final processedBytes = await compute(_processImageBytes, {
        'bytes': rawBytes,
        'quality': quality,
        'maxWidth': maxWidth,
      });

      return processedBytes ?? rawBytes;
    } catch (e) {
      debugPrint('CameraService: captureFrameJpeg error: $e');
      return null;
    } finally {
      _isCapturing = false;
    }
  }

  /// Stop and release all camera hardware resources.
  Future<void> dispose() async {
    final ctrl = _controller;
    _controller = null;
    if (ctrl != null) {
      try {
        await ctrl.dispose();
      } catch (e) {
        debugPrint('CameraService: Error disposing camera controller: $e');
      }
    }
  }
}

/// Standalone top-level function for background isolate image processing.
Uint8List? _processImageBytes(Map<String, dynamic> params) {
  final bytes = params['bytes'] as Uint8List;
  final quality = params['quality'] as int;
  final maxWidth = params['maxWidth'] as int;

  try {
    final decoded = img.decodeImage(bytes);
    if (decoded == null) return bytes;

    // Apply EXIF orientation to ensure upright orientation for spatial reasoning
    var oriented = img.bakeOrientation(decoded);

    // Downscale if width exceeds maximum threshold
    if (oriented.width > maxWidth) {
      oriented = img.copyResize(oriented, width: maxWidth);
    }

    final compressed = img.encodeJpg(oriented, quality: quality);
    return Uint8List.fromList(compressed);
  } catch (e) {
    return bytes;
  }
}
