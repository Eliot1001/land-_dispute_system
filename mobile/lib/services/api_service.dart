import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/app_config.dart';
import '../models/case_model.dart';
import '../models/profile_model.dart';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => message;
}

class ApiService {
  /// Backend base URL. Configured in one place: [AppConfig.baseUrl].
  static const String baseUrl = AppConfig.baseUrl;

  static String? _token;

  static Future<void> _loadToken() async {
    if (_token != null) return;
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token');
  }

  static Future<void> _saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('auth_token', token);
  }

  static Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
  }

  static Future<bool> hasToken() async {
    await _loadToken();
    return _token != null;
  }

  static Map<String, String> _headers() {
    return _token != null ? {'Authorization': 'Token $_token'} : {};
  }

  static dynamic _decode(http.Response response) {
    dynamic body;
    try {
      body = response.body.isNotEmpty ? jsonDecode(response.body) : {};
    } on FormatException {
      // Server returned HTML instead of JSON — Render free tier waking up,
      // or a gateway/proxy error page.
      throw ApiException(
        'The server is starting up. Please wait 30 seconds and try again.',
      );
    }
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }
    final message = (body is Map && body['error'] != null)
        ? body['error'].toString()
        : 'Request failed (${response.statusCode})';
    throw ApiException(message);
  }

  static Future<CitizenProfile> register({
    required String firstName,
    required String lastName,
    required String email,
    required String phone,
    required String username,
    required String password,
    String region = '',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register/'),
      body: {
        'first_name': firstName,
        'last_name': lastName,
        'email': email,
        'phone': phone,
        'username': username,
        'password': password,
        'region': region,
      },
    );
    final data = _decode(response);
    await _saveToken(data['token']);
    return CitizenProfile.fromJson(data['profile']);
  }

  static Future<CitizenProfile> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      body: {'username': username, 'password': password},
    );
    final data = _decode(response);
    await _saveToken(data['token']);
    return CitizenProfile.fromJson(data['profile']);
  }

  static Future<void> forgotPassword({
    required String username,
    required String identifier,
    required String newPassword,
    required String newPasswordConfirm,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/forgot-password/'),
      body: {
        'username': username,
        'identifier': identifier,
        'new_password': newPassword,
        'new_password_confirm': newPasswordConfirm,
      },
    );
    _decode(response);
  }

  static Future<void> logout() async {
    await _loadToken();
    try {
      await http.post(Uri.parse('$baseUrl/auth/logout/'), headers: _headers());
    } catch (_) {
      // Network errors don't matter here - the local token is cleared regardless.
    }
    await clearToken();
  }

  static Future<CitizenProfile> getProfile() async {
    await _loadToken();
    final response = await http.get(Uri.parse('$baseUrl/profile/'), headers: _headers());
    return CitizenProfile.fromJson(_decode(response));
  }

  static Future<CitizenProfile> updateProfile({
    required String firstName,
    required String lastName,
    required String email,
    required String phone,
  }) async {
    await _loadToken();
    final response = await http.put(
      Uri.parse('$baseUrl/profile/'),
      headers: _headers(),
      body: {
        'first_name': firstName,
        'last_name': lastName,
        'email': email,
        'phone': phone,
      },
    );
    return CitizenProfile.fromJson(_decode(response));
  }

  static Future<CaseListResult> getCases({String status = 'all'}) async {
    await _loadToken();
    final response = await http.get(
      Uri.parse('$baseUrl/cases/?status=$status'),
      headers: _headers(),
    );
    return CaseListResult.fromJson(_decode(response));
  }

  static Future<CaseDetail> getCaseDetail(int id) async {
    await _loadToken();
    final response = await http.get(Uri.parse('$baseUrl/cases/$id/'), headers: _headers());
    return CaseDetail.fromJson(_decode(response));
  }

  static Future<CaseDetail> submitCase({
    required String description,
    required String location,
    required String ward,
    required double latitude,
    required double longitude,
    List<PlatformFile> documents = const [],
  }) async {
    await _loadToken();
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/cases/'));
    request.headers.addAll(_headers());
    request.fields['description'] = description;
    request.fields['location'] = location;
    request.fields['ward'] = ward;
    request.fields['latitude'] = latitude.toString();
    request.fields['longitude'] = longitude.toString();

    for (final file in documents) {
      if (file.bytes != null) {
        request.files.add(http.MultipartFile.fromBytes('documents', file.bytes!, filename: file.name));
      } else if (file.path != null) {
        request.files.add(await http.MultipartFile.fromPath('documents', file.path!, filename: file.name));
      }
    }

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return CaseDetail.fromJson(_decode(response));
  }

  static Future<CaseFeedback> submitCaseFeedback({
    required int caseId,
    required String rating,
    String comment = '',
  }) async {
    await _loadToken();
    final response = await http.post(
      Uri.parse('$baseUrl/cases/$caseId/feedback/'),
      headers: _headers(),
      body: {'rating': rating, 'comment': comment},
    );
    return CaseFeedback.fromJson(_decode(response));
  }

  static Future<List<int>> downloadDocument(int documentId) async {
    await _loadToken();
    final response = await http.get(
      Uri.parse('$baseUrl/documents/$documentId/download/'),
      headers: _headers(),
    );
    if (response.statusCode != 200) {
      throw ApiException('Could not download this document (${response.statusCode})');
    }
    return response.bodyBytes;
  }
}
