
import 'dart:io';
import 'dart:js_interop';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

@JS('speakAssistance')
external void speakAssistance(JSString message);

void main() {
  runApp(const AEyeApp());
}

class AEyeApp extends StatelessWidget {
  const AEyeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'A-Eye',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.teal,
        ),
        useMaterial3: true,
      ),
      home: const AssistanceScreen(),
    );
  }
}

class AssistanceScreen extends StatefulWidget {
  const AssistanceScreen({super.key});

  @override
  State<AssistanceScreen> createState() =>
      _AssistanceScreenState();
}

class _AssistanceScreenState extends State<AssistanceScreen> {
  final ImagePicker picker = ImagePicker();

  XFile? selectedImage;
  String response =
      'Select an image and request assistance.';
  bool isProcessing = false;

  void speakResponse() {
    if (kIsWeb) {
      speakAssistance(response.toJS);
    }
  }

  Future<void> chooseImage() async {
    final XFile? image = await picker.pickImage(
      source: ImageSource.gallery,
    );

    if (image != null && mounted) {
      setState(() {
        selectedImage = image;
        response =
            'Image selected. Ready to request assistance.';
      });
    }
  }

  Future<void> getAssistance() async {
    if (selectedImage == null) {
      setState(() {
        response = 'Please select an image first.';
      });
      return;
    }

    setState(() {
      isProcessing = true;
      response = 'Processing your request...';
    });

    await Future.delayed(
      const Duration(seconds: 1),
    );

    if (!mounted) return;

    setState(() {
      isProcessing = false;
      response =
          'Demo response: An obstacle may be ahead. '
          'Please proceed carefully.';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'A-Eye',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: 520,
            ),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.stretch,
              children: [
                const Icon(
                  Icons.visibility_outlined,
                  size: 72,
                  color: Colors.teal,
                ),
                const SizedBox(height: 12),
                const Text(
                  'AI-Powered Visual Assistance',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Helping users understand their surroundings',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.teal.withValues(
                      alpha: 0.08,
                    ),
                    borderRadius:
                        BorderRadius.circular(16),
                    border: Border.all(
                      color: Colors.teal.shade200,
                    ),
                  ),
                  child: Column(
                    children: [
                      if (selectedImage != null)
                        ClipRRect(
                          borderRadius:
                              BorderRadius.circular(12),
                          child: kIsWeb
                              ? Image.network(
                                  selectedImage!.path,
                                  height: 220,
                                  width: double.infinity,
                                  fit: BoxFit.contain,
                                )
                              : Image.file(
                                  File(selectedImage!.path),
                                  height: 220,
                                  width: double.infinity,
                                  fit: BoxFit.contain,
                                ),
                        )
                      else
                        const Icon(
                          Icons.add_photo_alternate_outlined,
                          size: 64,
                          color: Colors.teal,
                        ),
                      const SizedBox(height: 12),
                      const Text(
                        'Camera / Image Input',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: chooseImage,
                        icon: const Icon(Icons.image_outlined),
                        label: const Text('Choose Image'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed:
                      isProcessing ? null : getAssistance,
                  icon: const Icon(Icons.assistant),
                  label: Text(
                    isProcessing
                        ? 'Processing...'
                        : 'Get Assistance',
                  ),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.all(18),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: speakResponse,
                  icon: const Icon(Icons.volume_up),
                  label: const Text('Speak Assistance'),
                ),
                const SizedBox(height: 24),
                const Text(
                  'ASSISTANCE OUTPUT',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: Colors.grey.withValues(
                      alpha: 0.10,
                    ),
                    borderRadius:
                        BorderRadius.circular(12),
                  ),
                  child: Row(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.record_voice_over),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          response,
                          style: const TextStyle(
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Prototype: assistance output is simulated '
                  'and is not generated by a real AI model.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
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
