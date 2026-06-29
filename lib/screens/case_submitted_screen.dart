import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/case_model.dart';
import '../theme.dart';
import 'case_detail_screen.dart';
import 'dashboard_screen.dart';

class CaseSubmittedScreen extends StatelessWidget {
  final CaseDetail caseDetail;
  const CaseSubmittedScreen({super.key, required this.caseDetail});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Container(
              padding: const EdgeInsets.symmetric(vertical: 36),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF27AE60), Color(0xFF229954)]),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Column(
                children: [
                  Icon(Icons.check_circle, color: Colors.white, size: 56),
                  SizedBox(height: 12),
                  Text(
                    'Case Submitted Successfully!',
                    style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Your land dispute case has been successfully submitted. A dedicated officer in your '
              'region has been automatically assigned to handle your case.',
              style: TextStyle(color: Colors.grey, height: 1.4),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _infoRow('Case ID', '#${caseDetail.id}'),
                    _infoRow('Case Title', caseDetail.title),
                    _infoRow('Location', caseDetail.location),
                    _infoRow('Region', caseDetail.regionDisplay),
                    _infoRow('Assigned Officer', caseDetail.assignedOfficer ?? 'Pending Assignment'),
                    _infoRow('Submitted On', DateFormat.yMMMd().add_jm().format(caseDetail.createdAt), isLast: true),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text('What Happens Next?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            _step(Icons.check, '1', 'Case Received', 'Your case has been registered in the system'),
            _step(Icons.search, '2', 'Officer Review', 'The assigned officer will review your case details'),
            _step(Icons.fact_check, '3', 'Investigation', 'The case will be investigated and processed'),
            _step(Icons.flag, '4', 'Resolution', 'Updates will be provided as your case progresses'),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(builder: (_) => const DashboardScreen()),
                      (route) => false,
                    ),
                    child: const Text('Dashboard'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => Navigator.of(context).pushReplacement(
                      MaterialPageRoute(builder: (_) => CaseDetailScreen(caseId: caseDetail.id)),
                    ),
                    child: const Text('View Details'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(String label, String value, {bool isLast = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        border: isLast ? null : const Border(bottom: BorderSide(color: Color(0xFFECF0F1))),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w600, fontSize: 13)),
          Flexible(
            child: Text(value, textAlign: TextAlign.right, style: const TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }

  Widget _step(IconData icon, String number, String title, String description) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(radius: 16, backgroundColor: const Color(0xFF27AE60), child: Icon(icon, color: Colors.white, size: 16)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                Text(description, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
