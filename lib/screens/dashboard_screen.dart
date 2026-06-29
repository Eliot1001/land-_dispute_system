import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/case_model.dart';
import '../services/api_service.dart';
import '../theme.dart';
import 'case_detail_screen.dart';
import 'login_screen.dart';
import 'profile_screen.dart';
import 'submit_case_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  String _filterStatus = 'all';
  CaseListResult? _result;
  bool _loading = true;
  String? _error;

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
      final result = await ApiService.getCases(status: _filterStatus);
      setState(() => _result = result);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    await ApiService.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final counts = _result?.counts ?? {};
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Cases'),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: _logout),
        ],
      ),
      drawer: _buildDrawer(),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _buildBody(counts),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final submitted = await Navigator.of(context).push<bool>(
            MaterialPageRoute(builder: (_) => const SubmitCaseScreen()),
          );
          if (submitted == true) _load();
        },
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          Container(
            decoration: const BoxDecoration(gradient: AppColors.gradient),
            padding: const EdgeInsets.fromLTRB(20, 50, 20, 20),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('⚖️', style: TextStyle(fontSize: 36)),
                SizedBox(height: 8),
                Text('Land Dispute', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                Text('Citizen Portal', style: TextStyle(color: Colors.white70, fontSize: 13)),
              ],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.gavel, color: AppColors.primary),
            title: const Text('My Cases'),
            onTap: () => Navigator.of(context).pop(),
          ),
          ListTile(
            leading: const Icon(Icons.add_circle_outline, color: AppColors.primary),
            title: const Text('Submit New Case'),
            onTap: () async {
              Navigator.of(context).pop();
              final submitted = await Navigator.of(context).push<bool>(
                MaterialPageRoute(builder: (_) => const SubmitCaseScreen()),
              );
              if (submitted == true) _load();
            },
          ),
          ListTile(
            leading: const Icon(Icons.person_outline, color: AppColors.primary),
            title: const Text('My Profile'),
            onTap: () {
              Navigator.of(context).pop();
              Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ProfileScreen()));
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Sign Out', style: TextStyle(color: Colors.red)),
            onTap: () {
              Navigator.of(context).pop();
              _logout();
            },
          ),
        ],
      ),
    );
  }

  Widget _buildBody(Map<String, int> counts) {
    if (_loading && _result == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null && _result == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(_error!, style: TextStyle(color: Colors.red.shade800)),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );
    }

    final cases = _result?.results ?? [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            _countCard('Pending', counts['pending'] ?? 0, AppColors.statusColors['pending']!),
            const SizedBox(width: 8),
            _countCard('In Progress', counts['in_progress'] ?? 0, AppColors.statusColors['in_progress']!),
            const SizedBox(width: 8),
            _countCard('Resolved', counts['resolved'] ?? 0, AppColors.statusColors['resolved']!),
          ],
        ),
        const SizedBox(height: 16),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _filterChip('all', 'All'),
              _filterChip('pending', 'Pending'),
              _filterChip('in_progress', 'In Progress'),
              _filterChip('resolved', 'Resolved'),
              _filterChip('escalated', 'Escalated'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (cases.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 60),
            child: Center(
              child: Column(
                children: [
                  Icon(Icons.inbox_outlined, size: 48, color: Colors.grey.shade400),
                  const SizedBox(height: 8),
                  Text('No cases yet', style: TextStyle(color: Colors.grey.shade600)),
                ],
              ),
            ),
          )
        else
          ...cases.map(_caseCard),
      ],
    );
  }

  Widget _countCard(String label, int count, Color color) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Column(
            children: [
              Text('$count', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
              Text(label, style: const TextStyle(fontSize: 12), textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }

  Widget _filterChip(String value, String label) {
    final selected = _filterStatus == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) {
          setState(() => _filterStatus = value);
          _load();
        },
        selectedColor: AppColors.primary,
        labelStyle: TextStyle(color: selected ? Colors.white : Colors.black87),
      ),
    );
  }

  Widget _caseCard(CaseSummary c) {
    final color = AppColors.statusColors[c.status] ?? AppColors.primary;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => CaseDetailScreen(caseId: c.id))),
        leading: CircleAvatar(backgroundColor: color, child: const Icon(Icons.gavel, color: Colors.white, size: 18)),
        title: Text(c.title, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text('${c.location}\n${DateFormat.yMMMd().format(c.createdAt)}'),
        isThreeLine: true,
        trailing: Chip(
          label: Text(c.statusDisplay, style: const TextStyle(fontSize: 11, color: Colors.white)),
          backgroundColor: color,
          padding: EdgeInsets.zero,
        ),
      ),
    );
  }
}
