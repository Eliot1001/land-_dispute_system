import 'dart:convert';
import 'package:http/http.dart' as http;

class GeocodeService {
  // Nominatim's usage policy requires a descriptive User-Agent identifying the app.
  static const _userAgent = 'LandDisputeCitizenApp/1.0';

  static Future<String> reverseGeocode(double lat, double lng) async {
    try {
      final response = await http.get(
        Uri.parse('https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=$lat&lon=$lng'),
        headers: {'User-Agent': _userAgent},
      );
      if (response.statusCode != 200) {
        return 'Coordinates: ${lat.toStringAsFixed(6)}, ${lng.toStringAsFixed(6)}';
      }

      final data = jsonDecode(response.body);
      final address = (data['address'] ?? {}) as Map<String, dynamic>;

      final region = address['state'] ?? address['region'] ?? '';
      final district = address['county'] ?? address['town'] ?? address['city'] ?? '';
      final ward = address['suburb'] ??
          address['neighbourhood'] ??
          address['city_district'] ??
          address['village'] ??
          '';
      final street = address['road'] ?? '';

      final parts = [street, ward, district, region].where((p) => p.toString().isNotEmpty);
      final fullLocation = parts.join(', ');

      return fullLocation.isNotEmpty
          ? fullLocation
          : 'Coordinates: ${lat.toStringAsFixed(6)}, ${lng.toStringAsFixed(6)}';
    } catch (_) {
      return 'Coordinates: ${lat.toStringAsFixed(6)}, ${lng.toStringAsFixed(6)}';
    }
  }
}
