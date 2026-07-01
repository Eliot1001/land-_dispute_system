class CitizenProfile {
  final String username;
  final String firstName;
  final String lastName;
  final String email;
  final String phone;
  final String region;
  final DateTime? dateJoined;

  CitizenProfile({
    required this.username,
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.phone,
    required this.region,
    this.dateJoined,
  });

  factory CitizenProfile.fromJson(Map<String, dynamic> json) {
    return CitizenProfile(
      username: json['username'] ?? '',
      firstName: json['first_name'] ?? '',
      lastName: json['last_name'] ?? '',
      email: json['email'] ?? '',
      phone: json['phone'] ?? '',
      region: json['region'] ?? '',
      dateJoined: json['date_joined'] != null ? DateTime.tryParse(json['date_joined']) : null,
    );
  }

  String get fullName => '$firstName $lastName'.trim();
}
