

import 'dart:convert';

import 'dart:typed_data';



import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

import 'package:flutter_tts/flutter_tts.dart';

import 'package:http/http.dart' as http;

import 'package:image_picker/image_picker.dart';



void main() {

  runApp(const AEyeApp());

}



class AEyeApp extends StatelessWidget {

  const AEyeApp({super.key});



  @override

  Widget build(BuildContext context) {

    return MaterialApp(

      title: 'A-Eye',

      debugShowCheckedModeBanner: false,

      theme: ThemeData(

        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),

        useMaterial3: true,

      ),

      home: const AssistanceScreen(),

    );

  }

}



class AssistanceScreen extends StatefulWidget {

  const AssistanceScreen({super.key});



  @override

  State<AssistanceScreen> createState() => _AssistanceScreenState();

}



class _AssistanceScreenState extends State<AssistanceScreen> {

  final ImagePicker _picker = ImagePicker();

  final FlutterTts _tts = FlutterTts();



  XFile? _selectedImage;

  Uint8List? _imageBytes;



  bool _loading = false;

  bool _isSpeaking = false;



  String _message = 'Choose an image or take a photo to get assistance.';

  String _mode = '';



  @override

  void initState() {

    super.initState();

    _configureTts();

  }



  Future<void> _configureTts() async {

    await _tts.setLanguage('en-IN');

    await _tts.setSpeechRate(0.45);

    await _tts.setVolume(1.0);

    await _tts.setPitch(1.0);



    _tts.setStartHandler(() {

      if (mounted) {

        setState(() => _isSpeaking = true);

      }

    });



    _tts.setCompletionHandler(() {

      if (mounted) {

        setState(() => _isSpeaking = false);

      }

    });



    _tts.setCancelHandler(() {

      if (mounted) {

        setState(() => _isSpeaking = false);

      }

    });



    _tts.setErrorHandler((message) {

      if (mounted) {

        setState(() => _isSpeaking = false);

      }

    });

  }



  // Select an image from the gallery or capture a photo.

  Future<void> _chooseImage({

    ImageSource source = ImageSource.gallery,

  }) async {

    try {

      final image = await _picker.pickImage(

        source: source,

      );



      if (image == null) return;



      final bytes = await image.readAsBytes();



      await _stopSpeaking();



      if (!mounted) return;



      setState(() {

        _selectedImage = image;

        _imageBytes = bytes;

        _message = 'Image selected. Tap Get Assistance.';

        _mode = '';

      });

    } catch (e) {

      if (!mounted) return;



      setState(() {

        _message = 'Could not select or capture the image: $e';

      });

    }

  }




  // Open a live webcam preview and capture a photo.
  Future<void> _takePhotoWithCamera() async {
    CameraController? controller;
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw Exception('No camera was found on this device.');
      }

      controller = CameraController(
        cameras.first,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      await controller.initialize();

      if (!mounted) {
        await controller.dispose();
        return;
      }

      final capturedImage = await showDialog<XFile>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) {
          return AlertDialog(
            title: const Text('Take a photo'),
            content: SizedBox(
              width: 520,
              height: 360,
              child: CameraPreview(controller!),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(dialogContext).pop(),
                child: const Text('Cancel'),
              ),
              FilledButton.icon(
                onPressed: () async {
                  try {
                    final photo = await controller!.takePicture();
                    if (dialogContext.mounted) {
                      Navigator.of(dialogContext).pop(photo);
                    }
                  } catch (e) {
                    if (dialogContext.mounted) {
                      ScaffoldMessenger.of(dialogContext).showSnackBar(
                        SnackBar(content: Text('Could not capture photo: $e')),
                      );
                    }
                  }
                },
                icon: const Icon(Icons.camera_alt),
                label: const Text('Capture'),
              ),
            ],
          );
        },
      );

      if (capturedImage == null) return;
      final bytes = await capturedImage.readAsBytes();
      await _stopSpeaking();
      if (!mounted) return;

      setState(() {
        _selectedImage = capturedImage;
        _imageBytes = bytes;
        _message = 'Photo captured. Tap Get Assistance.';
        _mode = '';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _message = 'Could not open the camera. Check browser camera permission. Details: $e';
      });
    } finally {
      await controller?.dispose();
    }
  }

  Future<void> _clearImage() async {
    await _stopSpeaking();
    if (!mounted) return;
    setState(() {
      _selectedImage = null;
      _imageBytes = null;
      _mode = '';
      _message = 'Choose an image or take a photo to get assistance.';
    });
  }

  Future<void> _getAssistance() async {

    if (_selectedImage == null || _imageBytes == null) {

      setState(() {

        _message = 'Please choose an image or take a photo first.';

      });

      return;

    }



    await _stopSpeaking();



    setState(() {

      _loading = true;

      _message = 'Sending image to A-Eye backend...';

      _mode = '';

    });



    try {

      final uri = Uri.parse('http://127.0.0.1:5000/analyze');



      final request = http.MultipartRequest('POST', uri);



      request.files.add(

        http.MultipartFile.fromBytes(

          'image',

          _imageBytes!,

          filename: _selectedImage!.name,

        ),

      );



      final streamedResponse = await request.send().timeout(

        const Duration(seconds: 60),

      );



      final response = await http.Response.fromStream(streamedResponse);

      final dynamic decoded = jsonDecode(response.body);



      if (decoded is! Map<String, dynamic>) {

        throw const FormatException(

          'Unexpected response from backend.',

        );

      }



      if (response.statusCode >= 200 &&

          response.statusCode < 300) {

        if (!mounted) return;



        setState(() {

          _mode = (decoded['mode']?.toString() ?? 'unknown').toLowerCase();

          _message =

              decoded['assistance_message']?.toString() ??

              decoded['summary']?.toString() ??

              'The backend returned no assistance message.';

        });

      } else {

        if (!mounted) return;



        setState(() {

          _message =

              decoded['error']?.toString() ??

              'Backend error: ${response.statusCode}';

        });

      }

    } catch (e) {

      if (!mounted) return;



      setState(() {

        _message =

            'Could not contact the backend. Check that the Python '

            'server is running. Details: $e';

      });

    } finally {

      if (mounted) {

        setState(() => _loading = false);

      }

    }

  }



  Future<void> _speakAssistance() async {

    final text = _message.trim();



    if (text.isEmpty) return;



    try {

      await _tts.stop();

      await _tts.speak(text);

    } catch (e) {

      if (!mounted) return;



      ScaffoldMessenger.of(context).showSnackBar(

        SnackBar(

          content: Text('Could not speak the response: $e'),

        ),

      );

    }

  }



  Future<void> _stopSpeaking() async {

    try {

      await _tts.stop();

    } catch (_) {

      // Keep the app usable if speech cannot be stopped.

    }



    if (mounted) {

      setState(() => _isSpeaking = false);

    }

  }



  @override

  void dispose() {

    _tts.stop();

    super.dispose();

  }



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      appBar: AppBar(

        title: const Text('A-Eye — Visual Assistance'),

        centerTitle: true,

      ),

      body: Center(

        child: SingleChildScrollView(

          padding: const EdgeInsets.all(24),

          child: ConstrainedBox(

            constraints: const BoxConstraints(maxWidth: 600),

            child: Column(

              crossAxisAlignment: CrossAxisAlignment.stretch,

              children: [

                const Icon(

                  Icons.visibility,

                  size: 64,

                  color: Colors.teal,

                ),

                const SizedBox(height: 12),

                const Text(

                  'AI-powered assistance',

                  textAlign: TextAlign.center,

                  style: TextStyle(

                    fontSize: 24,

                    fontWeight: FontWeight.bold,

                  ),

                ),

                const SizedBox(height: 12),

                Card(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  child: const Padding(
                    padding: EdgeInsets.all(12),
                    child: Text(
                      'Assistive aid only. Always use your usual mobility aid and training. '
                      'Visual descriptions can be incomplete or incorrect.',
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                // Choose an existing image.

                OutlinedButton.icon(

                  onPressed: _loading

                      ? null

                      : () => _chooseImage(

                            source: ImageSource.gallery,

                          ),

                  icon: const Icon(Icons.image),

                  label: const Text('Choose Image'),

                ),



                const SizedBox(height: 8),



                // Capture a photo using the camera.

                OutlinedButton.icon(

                  onPressed: _loading ? null : _takePhotoWithCamera,

                  icon: const Icon(Icons.camera_alt),

                  label: const Text('Take Photo'),

                ),



                if (_imageBytes != null) ...[

                  const SizedBox(height: 16),

                  ClipRRect(

                    borderRadius: BorderRadius.circular(12),

                    child: Image.memory(

                      _imageBytes!,

                      height: 260,

                      fit: BoxFit.contain,

                    ),

                  ),

                ],

                if (_imageBytes != null) ...[
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: _loading ? null : _clearImage,
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Remove Image'),
                  ),
                ],

                const SizedBox(height: 16),

                FilledButton.icon(

                  onPressed: _loading ? null : _getAssistance,

                  icon: const Icon(Icons.record_voice_over),

                  label: Text(

                    _loading ? 'Processing...' : 'Get Assistance',

                  ),

                ),



                const SizedBox(height: 24),



                Card(

                  child: Padding(

                    padding: const EdgeInsets.all(20),

                    child: Column(

                      crossAxisAlignment: CrossAxisAlignment.start,

                      children: [

                        const Text(

                          'Assistance Response',

                          style: TextStyle(

                            fontSize: 18,

                            fontWeight: FontWeight.bold,

                          ),

                        ),

                        const SizedBox(height: 12),



                        if (_loading)

                          const LinearProgressIndicator(),



                        const SizedBox(height: 8),

                        Text(_message),



                        if (_mode.isNotEmpty) ...[

                          const SizedBox(height: 12),

                          Text('Backend mode: $_mode'),



                          if (_mode.contains('mock'))

                            const Text(

                              'Demo only: this is a simulated response, '

                              'not real image analysis. Do not use it to navigate.',

                              style: TextStyle(

                                color: Colors.deepOrange,

                              ),

                            ),

                        ],



                        const SizedBox(height: 20),



                        SizedBox(

                          width: double.infinity,

                          child: FilledButton.icon(

                            onPressed: _loading || _isSpeaking

                                ? null

                                : _speakAssistance,

                            icon: const Icon(Icons.volume_up),

                            label: const Text('Speak Assistance'),

                          ),

                        ),



                        const SizedBox(height: 8),



                        SizedBox(

                          width: double.infinity,

                          child: OutlinedButton.icon(

                            onPressed: _stopSpeaking,

                            icon: const Icon(Icons.stop),

                            label: const Text('Stop Speaking'),

                          ),

                        ),

                      ],

                    ),

                  ),

                ),

              ],

            ),

          ),

        ),

      ),

    );

  }

}
