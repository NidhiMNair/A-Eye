package com.aeye.track3_app

import android.view.WindowManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "com.aeye.track3_app/screen_curtain"
    private var isCurtainActive = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "enableCurtain" -> {
                    enableScreenCurtain()
                    result.success(true)
                }
                "disableCurtain" -> {
                    disableScreenCurtain()
                    result.success(true)
                }
                "isCurtainActive" -> {
                    result.success(isCurtainActive)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun enableScreenCurtain() {
        runOnUiThread {
            val lp = window.attributes
            lp.screenBrightness = 0.01f // Minimum backlight without powering panel off
            window.attributes = lp
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            isCurtainActive = true
        }
    }

    private fun disableScreenCurtain() {
        runOnUiThread {
            val lp = window.attributes
            lp.screenBrightness = WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE // Restore system brightness
            window.attributes = lp
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            isCurtainActive = false
        }
    }

    override fun onPause() {
        super.onPause()
        if (isCurtainActive) {
            disableScreenCurtain()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        disableScreenCurtain()
    }
}
