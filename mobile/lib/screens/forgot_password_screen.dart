import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _codeController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _newPasswordConfirmController = TextEditingController();

  bool _loading = false;
  String? _error;
  String? _info;
  bool _codeRequested = false;
  bool _success = false;

  Future<void> _requestCode() async {
    if (_usernameController.text.trim().isEmpty || _emailController.text.trim().isEmpty) {
      setState(() => _error = 'Please enter your username and email');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ApiService.requestPasswordResetCode(
        username: _usernameController.text.trim(),
        email: _emailController.text.trim(),
      );
      if (!mounted) return;
      setState(() {
        _codeRequested = true;
        _info = 'If that account exists, a reset code has been emailed to it. Enter the code below.';
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _confirmReset() async {
    if ([
      _codeController.text,
      _newPasswordController.text,
      _newPasswordConfirmController.text,
    ].any((v) => v.trim().isEmpty)) {
      setState(() => _error = 'Please fill in all fields');
      return;
    }
    if (_newPasswordController.text != _newPasswordConfirmController.text) {
      setState(() => _error = 'Passwords do not match');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ApiService.confirmPasswordReset(
        username: _usernameController.text.trim(),
        code: _codeController.text.trim(),
        newPassword: _newPasswordController.text,
        newPasswordConfirm: _newPasswordConfirmController.text,
      );
      if (!mounted) return;
      setState(() => _success = true);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _codeController.dispose();
    _newPasswordController.dispose();
    _newPasswordConfirmController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot Password')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_success) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.green.shade50, borderRadius: BorderRadius.circular(8)),
                child: Text(
                  'Password reset successful. You can now log in with your new password.',
                  style: TextStyle(color: Colors.green.shade800),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Back to Login'),
              ),
            ] else ...[
              if (_error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)),
                  child: Text(_error!, style: TextStyle(color: Colors.red.shade800)),
                ),
                const SizedBox(height: 16),
              ],
              if (_info != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
                  child: Text(_info!, style: TextStyle(color: Colors.blue.shade800)),
                ),
                const SizedBox(height: 16),
              ],
              if (!_codeRequested) ...[
                const Text('Enter your username and registered email. We will email you a reset code.'),
                const SizedBox(height: 16),
                TextField(
                  controller: _usernameController,
                  decoration: const InputDecoration(labelText: 'Username'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Registered Email'),
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _loading ? null : _requestCode,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Send Reset Code'),
                ),
              ] else ...[
                TextField(
                  controller: _codeController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: '6-Digit Code'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _newPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'New Password'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _newPasswordConfirmController,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Confirm New Password'),
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _loading ? null : _confirmReset,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Reset Password'),
                ),
                TextButton(
                  onPressed: _loading
                      ? null
                      : () => setState(() {
                            _codeRequested = false;
                            _info = null;
                          }),
                  child: const Text('Use a different username or email'),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}
