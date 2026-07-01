/// Single source of truth for the backend URL. Change [baseUrl] here only.
class AppConfig {
  AppConfig._();

  // Production — deployed Render backend (HTTPS, works on any device).
  static const String _prodUrl =
      'https://land-dispute-system-ghgp.onrender.com/api';

  // Local dev (Android emulator) — emulator reaches the host machine at 10.0.2.2.
  // For a real device over USB: use http://127.0.0.1:8000/api and run
  //   adb reverse tcp:8000 tcp:8000
  // before launching the app.
  // Requires cleartext HTTP allowed in android/app/src/debug/AndroidManifest.xml.
  // ignore: unused_field
  static const String _localUrl = 'http://10.0.2.2:8000/api';

  /// Swap to [_localUrl] when testing against a locally-running Django server.
  static const String baseUrl = _prodUrl;
}
