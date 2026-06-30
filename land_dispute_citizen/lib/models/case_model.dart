class CaseDocument {
  final int id;
  final String title;
  final String documentType;
  final String fileExtension;
  final double fileSizeMb;
  final DateTime uploadedAt;

  CaseDocument({
    required this.id,
    required this.title,
    required this.documentType,
    required this.fileExtension,
    required this.fileSizeMb,
    required this.uploadedAt,
  });

  factory CaseDocument.fromJson(Map<String, dynamic> json) {
    return CaseDocument(
      id: json['id'],
      title: json['title'] ?? '',
      documentType: json['document_type'] ?? '',
      fileExtension: json['file_extension'] ?? '',
      fileSizeMb: (json['file_size_mb'] as num?)?.toDouble() ?? 0,
      uploadedAt: DateTime.parse(json['uploaded_at']),
    );
  }
}

class CaseSummary {
  final int id;
  final String title;
  final String status;
  final String statusDisplay;
  final String region;
  final String regionDisplay;
  final String location;
  final DateTime createdAt;
  final DateTime updatedAt;
  // Escalation never changes `status` (it stays pending/in_progress/resolved)
  // - it only moves the case to a higher authority level. Use these to show
  // that separately instead of treating "escalated" as a status value.
  final bool isEscalated;
  final String currentLevelDisplay;

  CaseSummary({
    required this.id,
    required this.title,
    required this.status,
    required this.statusDisplay,
    required this.region,
    required this.regionDisplay,
    required this.location,
    required this.createdAt,
    required this.updatedAt,
    required this.isEscalated,
    required this.currentLevelDisplay,
  });

  factory CaseSummary.fromJson(Map<String, dynamic> json) {
    return CaseSummary(
      id: json['id'],
      title: json['title'] ?? '',
      status: json['status'] ?? '',
      statusDisplay: json['status_display'] ?? '',
      region: json['region'] ?? '',
      regionDisplay: json['region_display'] ?? '',
      location: json['location'] ?? '',
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      isEscalated: json['is_escalated'] ?? false,
      currentLevelDisplay: json['current_level_display'] ?? '',
    );
  }
}

class CaseDetail extends CaseSummary {
  final String description;
  final double latitude;
  final double longitude;
  final String notes;
  final String? assignedOfficer;
  final List<CaseDocument> documents;

  CaseDetail({
    required super.id,
    required super.title,
    required super.status,
    required super.statusDisplay,
    required super.region,
    required super.regionDisplay,
    required super.location,
    required super.createdAt,
    required super.updatedAt,
    required super.isEscalated,
    required super.currentLevelDisplay,
    required this.description,
    required this.latitude,
    required this.longitude,
    required this.notes,
    required this.assignedOfficer,
    required this.documents,
  });

  factory CaseDetail.fromJson(Map<String, dynamic> json) {
    return CaseDetail(
      id: json['id'],
      title: json['title'] ?? '',
      status: json['status'] ?? '',
      statusDisplay: json['status_display'] ?? '',
      region: json['region'] ?? '',
      regionDisplay: json['region_display'] ?? '',
      location: json['location'] ?? '',
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      isEscalated: json['is_escalated'] ?? false,
      currentLevelDisplay: json['current_level_display'] ?? '',
      description: json['description'] ?? '',
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      notes: json['notes'] ?? '',
      assignedOfficer: json['assigned_officer'],
      documents: (json['documents'] as List<dynamic>? ?? [])
          .map((d) => CaseDocument.fromJson(d))
          .toList(),
    );
  }
}

class CaseListResult {
  final Map<String, int> counts;
  final List<CaseSummary> results;

  CaseListResult({required this.counts, required this.results});

  factory CaseListResult.fromJson(Map<String, dynamic> json) {
    final counts = Map<String, int>.from(json['counts'] ?? {});
    final results = (json['results'] as List<dynamic>? ?? [])
        .map((c) => CaseSummary.fromJson(c))
        .toList();
    return CaseListResult(counts: counts, results: results);
  }
}
