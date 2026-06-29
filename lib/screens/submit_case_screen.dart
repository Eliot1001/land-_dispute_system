import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' as ll;

import '../services/api_service.dart';
import '../services/geocode_service.dart';
import '../services/location_service.dart';
import '../theme.dart';
import 'case_submitted_screen.dart';

class SubmitCaseScreen extends StatefulWidget {
  const SubmitCaseScreen({super.key});

  @override
  State<SubmitCaseScreen> createState() => _SubmitCaseScreenState();
}

class _SubmitCaseScreenState extends State<SubmitCaseScreen> {
  static const _tanzaniaCenter = ll.LatLng(-6.3690, 34.8888);

  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _mapController = MapController();

  ll.LatLng? _pinned;
  double? _accuracy;
  String _detectedLocation = '';
  final List<PlatformFile> _documents = [];

  bool _locating = false;
  bool _submitting = false;
  String? _error;

  Future<void> _useCurrentLocation() async {
    setState(() {
      _locating = true;
      _error = null;
    });
    try {
      final position = await LocationService.getBestLocation();
      await _setPinned(ll.LatLng(position.latitude, position.longitude), accuracy: position.accuracy);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  Future<void> _setPinned(ll.LatLng point, {double? accuracy}) async {
    setState(() {
      _pinned = point;
      _accuracy = accuracy;
    });
    _mapController.move(point, 16);
    final location = await GeocodeService.reverseGeocode(point.latitude, point.longitude);
    if (mounted) setState(() => _detectedLocation = location);
  }

  Future<void> _pickDocuments() async {
    final result = await FilePicker.pickFiles(allowMultiple: true, withData: true);
    if (result == null) return;
    final tooLarge = result.files.where((f) => f.size > 5 * 1024 * 1024).toList();
    final accepted = result.files.where((f) => f.size <= 5 * 1024 * 1024).toList();
    setState(() => _documents.addAll(accepted));
    if (tooLarge.isNotEmpty && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Skipped ${tooLarge.length} file(s) over 5MB')),
      );
    }
  }

  Future<void> _submit() async {
    if (_titleController.text.trim().isEmpty || _descriptionController.text.trim().isEmpty) {
      setState(() => _error = 'Please fill in the title and description');
      return;
    }
    if (_pinned == null) {
      setState(() => _error = 'Please pin your location on the map, or tap "Get My Location"');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final created = await ApiService.submitCase(
        title: _titleController.text.trim(),
        description: _descriptionController.text.trim(),
        location: _detectedLocation.isNotEmpty
            ? _detectedLocation
            : 'Coordinates: ${_pinned!.latitude.toStringAsFixed(6)}, ${_pinned!.longitude.toStringAsFixed(6)}',
        latitude: _pinned!.latitude,
        longitude: _pinned!.longitude,
        documents: _documents,
      );
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => CaseSubmittedScreen(caseDetail: created)),
      );
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Submit a Case')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)),
              child: Text(_error!, style: TextStyle(color: Colors.red.shade800)),
            ),
            const SizedBox(height: 16),
          ],
          TextField(
            controller: _titleController,
            decoration: const InputDecoration(labelText: 'Case Title', hintText: 'e.g. Boundary dispute over plot'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _descriptionController,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Description',
              hintText: 'Describe the dispute in detail',
            ),
          ),
          const SizedBox(height: 16),
          const Text('Location', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _locating ? null : _useCurrentLocation,
            icon: _locating
                ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.my_location),
            label: Text(_locating ? 'Pinpointing your location...' : 'Get My Current Location'),
          ),
          const SizedBox(height: 4),
          const Text(
            'Or tap on the map to pin the location manually',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: SizedBox(
              height: 280,
              child: FlutterMap(
                mapController: _mapController,
                options: MapOptions(
                  initialCenter: _pinned ?? _tanzaniaCenter,
                  initialZoom: _pinned != null ? 16 : 6,
                  maxZoom: 19,
                  onTap: (_, point) => _setPinned(point),
                ),
                children: [
                  TileLayer(
                    urlTemplate: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
                    subdomains: const ['a', 'b', 'c'],
                    userAgentPackageName: 'com.landdispute.land_dispute_citizen',
                    maxNativeZoom: 19,
                    maxZoom: 19,
                    retinaMode: RetinaMode.isHighDensity(context),
                  ),
                  if (_pinned != null && _accuracy != null)
                    CircleLayer(circles: [
                      CircleMarker(
                        point: _pinned!,
                        radius: _accuracy!,
                        useRadiusInMeter: true,
                        color: AppColors.secondary.withValues(alpha: 0.15),
                        borderColor: AppColors.secondary,
                        borderStrokeWidth: 1,
                      ),
                    ]),
                  if (_pinned != null)
                    MarkerLayer(markers: [
                      Marker(
                        point: _pinned!,
                        child: const Icon(Icons.location_pin, color: AppColors.secondary, size: 40),
                      ),
                    ]),
                ],
              ),
            ),
          ),
          if (_detectedLocation.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('📍 $_detectedLocation', style: const TextStyle(color: AppColors.secondary)),
            if (_accuracy != null)
              Text('GPS accuracy: ±${_accuracy!.round()}m', style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
          const SizedBox(height: 20),
          const Text('Evidence Documents (optional)', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _pickDocuments,
            icon: const Icon(Icons.attach_file),
            label: const Text('Attach Files'),
          ),
          ..._documents.asMap().entries.map((entry) {
            final i = entry.key;
            final file = entry.value;
            return ListTile(
              dense: true,
              leading: const Icon(Icons.insert_drive_file),
              title: Text(file.name, overflow: TextOverflow.ellipsis),
              subtitle: Text('${(file.size / (1024 * 1024)).toStringAsFixed(2)} MB'),
              trailing: IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => setState(() => _documents.removeAt(i)),
              ),
            );
          }),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _submitting ? null : _submit,
            child: _submitting
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Text('Submit Case'),
          ),
        ],
      ),
    );
  }
}
