import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:intl/intl.dart';
import 'package:latlong2/latlong.dart' as ll;
import 'package:path_provider/path_provider.dart';

import '../models/case_model.dart';
import '../services/api_service.dart';
import '../theme.dart';

class CaseDetailScreen extends StatefulWidget {
  final int caseId;
  const CaseDetailScreen({super.key, required this.caseId});

  @override
  State<CaseDetailScreen> createState() => _CaseDetailScreenState();
}

class _CaseDetailScreenState extends State<CaseDetailScreen> {
  CaseDetail? _caseDetail;
  bool _loading = true;
  String? _error;
  int? _downloadingDocId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final detail = await ApiService.getCaseDetail(widget.caseId);
      setState(() => _caseDetail = detail);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _downloadDocument(CaseDocument doc) async {
    setState(() => _downloadingDocId = doc.id);
    try {
      final bytes = await ApiService.downloadDocument(doc.id);
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/${doc.title}');
      await file.writeAsBytes(bytes);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Downloaded "${doc.title}" (${file.path})')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Download failed: $e')));
    } finally {
      if (mounted) setState(() => _downloadingDocId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Case Details')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: TextStyle(color: Colors.red.shade800)))
              : _buildDetail(_caseDetail!),
    );
  }

  Widget _buildDetail(CaseDetail c) {
    final color = AppColors.statusColors[c.status] ?? AppColors.primary;
    final showProgress = c.status != 'pending' || c.assignedOfficer != null || c.notes.isNotEmpty;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: Text(c.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            ),
            Chip(
              label: Text(c.statusDisplay, style: const TextStyle(color: Colors.white)),
              backgroundColor: color,
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (_statusBanner(c.status) != null) ...[_statusBanner(c.status)!, const SizedBox(height: 12)],
        _infoRow(Icons.description, 'Description', c.description),
        _infoRow(Icons.location_on, 'Location', c.location),
        _infoRow(Icons.map, 'Region', c.regionDisplay),
        _infoRow(Icons.my_location, 'Coordinates', '${c.latitude.toStringAsFixed(6)}, ${c.longitude.toStringAsFixed(6)}'),
        _infoRow(Icons.person, 'Assigned Officer', c.assignedOfficer ?? 'Pending assignment'),
        _infoRow(Icons.calendar_today, 'Submitted', DateFormat.yMMMd().add_jm().format(c.createdAt)),
        _infoRow(Icons.update, 'Last Updated', DateFormat.yMMMd().add_jm().format(c.updatedAt)),
        if (c.notes.isNotEmpty) _infoRow(Icons.notes, 'Officer Notes', c.notes),
        const SizedBox(height: 8),
        const Text('Case Location on Map', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: SizedBox(
            height: 220,
            child: FlutterMap(
              options: MapOptions(
                initialCenter: ll.LatLng(c.latitude, c.longitude),
                initialZoom: 14,
                maxZoom: 19,
                interactionOptions: const InteractionOptions(flags: InteractiveFlag.pinchZoom | InteractiveFlag.drag),
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
                MarkerLayer(markers: [
                  Marker(
                    point: ll.LatLng(c.latitude, c.longitude),
                    child: const Icon(Icons.location_pin, color: AppColors.secondary, size: 40),
                  ),
                ]),
              ],
            ),
          ),
        ),
        if (showProgress) ...[
          const SizedBox(height: 20),
          _progressSection(c),
        ],
        const SizedBox(height: 20),
        Text('Evidence Documents (${c.documents.length})', style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (c.documents.isEmpty)
          Text('No documents attached', style: TextStyle(color: Colors.grey.shade600))
        else
          ...c.documents.map((doc) => Card(
                child: ListTile(
                  leading: Icon(_documentIcon(doc.fileExtension)),
                  title: Text(doc.title, overflow: TextOverflow.ellipsis),
                  subtitle: Text('${doc.fileSizeMb.toStringAsFixed(2)} MB · ${DateFormat.yMMMd().format(doc.uploadedAt)}'),
                  trailing: _downloadingDocId == doc.id
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : IconButton(icon: const Icon(Icons.download), onPressed: () => _downloadDocument(doc)),
                ),
              )),
      ],
    );
  }

  IconData _documentIcon(String extension) {
    final ext = extension.toLowerCase();
    if (ext == 'pdf') return Icons.picture_as_pdf;
    if (['jpg', 'jpeg', 'png'].contains(ext)) return Icons.image;
    if (['doc', 'docx'].contains(ext)) return Icons.description;
    return Icons.insert_drive_file;
  }

  Widget? _statusBanner(String status) {
    final banners = {
      'in_progress': (
        Icons.settings,
        const Color(0xFF3498DB),
        'Your Case is Being Processed',
        'Our officer is actively working on your case. Check back soon for updates.',
      ),
      'escalated': (
        Icons.arrow_upward,
        const Color(0xFFE74C3C),
        'Case Escalated to Higher Authority',
        'This case requires higher-level review and decision-making.',
      ),
      'resolved': (
        Icons.check_circle,
        const Color(0xFF27AE60),
        'Your Case Has Been Resolved',
        'Thank you for using our service. If you have questions, contact our support team.',
      ),
    };
    final banner = banners[status];
    if (banner == null) return null;
    final (icon, color, title, subtitle) = banner;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border(left: BorderSide(color: color, width: 4)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 26),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _progressSection(CaseDetail c) {
    final assigned = c.assignedOfficer != null;
    final processing = c.status == 'in_progress' || c.status == 'escalated';
    final resolved = c.status == 'resolved';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Case Progress', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Row(
              children: [
                _progressStep('Submitted', true, true),
                _progressConnector(assigned || processing || resolved),
                _progressStep('Assigned', assigned, assigned),
                _progressConnector(processing || resolved),
                _progressStep('Processing', processing || resolved, processing),
                _progressConnector(resolved),
                _progressStep('Resolved', resolved, false),
              ],
            ),
            const SizedBox(height: 20),
            _timelineEvent(Icons.check, 'Case Submitted', DateFormat.yMMMd().add_jm().format(c.createdAt)),
            if (assigned)
              _timelineEvent(Icons.person, 'Officer Assigned', '${c.assignedOfficer} - ${c.regionDisplay}'),
            if (c.status != 'pending')
              _timelineEvent(Icons.flag, 'Status: ${c.statusDisplay}', DateFormat.yMMMd().add_jm().format(c.updatedAt)),
            if (c.notes.isNotEmpty) _timelineEvent(Icons.notes, 'Officer Notes', c.notes, isLast: true),
          ],
        ),
      ),
    );
  }

  Widget _progressStep(String label, bool completed, bool active) {
    final color = completed ? const Color(0xFF27AE60) : (active ? AppColors.primary : Colors.grey.shade300);
    return Expanded(
      child: Column(
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: color,
            child: completed
                ? const Icon(Icons.check, color: Colors.white, size: 14)
                : Text('', style: const TextStyle(color: Colors.white)),
          ),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(fontSize: 10, color: completed || active ? Colors.black87 : Colors.grey)),
        ],
      ),
    );
  }

  Widget _progressConnector(bool active) {
    return Expanded(
      child: Container(height: 2, color: active ? const Color(0xFF27AE60) : Colors.grey.shade300),
    );
  }

  Widget _timelineEvent(IconData icon, String title, String subtitle, {bool isLast = false}) {
    return Padding(
      padding: EdgeInsets.only(bottom: isLast ? 0 : 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: AppColors.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: AppColors.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                Text(value, style: const TextStyle(fontSize: 15)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
