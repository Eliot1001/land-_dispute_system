/// Single source of truth for the backend URL. Change it here only.
///
/// Release builds always use the deployed Render backend — no PC required.
/// For local debug testing over USB: change to 'http://127.0.0.1:8000/api'
/// and run `adb reverse tcp:8000 tcp:8000` before launching the app.
class AppConfig {
  AppConfig._();

  static const String baseUrl = 'http://127.0.0.1:8000/api';
}
