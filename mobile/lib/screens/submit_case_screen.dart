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

  final _descriptionController = TextEditingController();
  final _wardController = TextEditingController();
  final _mapController = MapController();

  ll.LatLng? _pinned;
  double? _accuracy;
  String _detectedLocation = '';
  final List<PlatformFile> _documents = [];

  bool _locating = false;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    // Detect the citizen's location as soon as the screen opens, so they
    // don't have to press "Get My Location" themselves.
    _useCurrentLocation();
  }

  Future<void> _useCurrentLocation() async {
    setState(() {
      _locating = true;
      _error = null;
    });
    try {
      // Show a cached fix immediately so the map isn't blank while a fresh,
      // more accurate GPS lock is still being acquired in the background.
      final cached = await LocationService.getLastKnownLocation();
      if (cached != null && mounted) {
        await _setPinned(ll.LatLng(cached.latitude, cached.longitude), accuracy: cached.accuracy);
      }

      final position = await LocationService.getBestLocation();
      if (!mounted) return;
      await _setPinned(ll.LatLng(position.latitude, position.longitude), accuracy: position.accuracy);
    } catch (e) {
      // A cached fix already on screen is still usable, so don't blank it
      // out with an error - the citizen can retry or pin manually either way.
      if (_pinned == null) setState(() => _error = e.toString());
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
    if (_descriptionController.text.trim().isEmpty) {
      setState(() => _error = 'Please fill in the description');
      return;
    }
    if (_wardController.text.trim().isEmpty) {
      setState(() => _error = 'Please enter your ward or village');
      return;
    }
    if (_pinned == null) {
      setState(() => _error = 'Please pin your location on the map');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final created = await ApiService.submitCase(
        description: _descriptionController.text.trim(),
        location: _detectedLocation.isNotEmpty
            ? _detectedLocation
            : 'Coordinates: ${_pinned!.latitude.toStringAsFixed(6)}, ${_pinned!.longitude.toStringAsFixed(6)}',
        ward: _wardController.text.trim(),
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
    _descriptionController.dispose();
    _wardController.dispose();
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
            controller: _descriptionController,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Description',
              hintText: 'Describe the dispute in detail',
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _wardController,
            decoration: const InputDecoration(
              labelText: 'Ward / Village',
              hintText: 'Where are you coming from?',
            ),
          ),
          const SizedBox(height: 16),
          const Text('Location', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(
            _locating ? 'Pinpointing your location...' : 'Tap on the map to pin your location',
            style: const TextStyle(fontSize: 12, color: Colors.grey),
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
