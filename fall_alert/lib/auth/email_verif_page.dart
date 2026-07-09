import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'signup_page.dart';

class EmailVerificationPage extends StatefulWidget {
  const EmailVerificationPage({super.key});

  @override
  State<EmailVerificationPage> createState() => _EmailVerificationPageState();
}

class _EmailVerificationPageState extends State<EmailVerificationPage> {
  Timer? _timer;
  bool _isSending = false;
  String? _message;

  @override
  void initState() {
    super.initState();

    _timer = Timer.periodic(const Duration(seconds: 3), (_) async {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) return;

      await user.reload();

      if (user.emailVerified) {
        _timer?.cancel();

        if (mounted) {
          setState(() {});
        }
      }
    });
  }

  Future<void> _resendVerificationEmail() async {
    setState(() {
      _isSending = true;
      _message = null;
    });

    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        throw Exception('No authenticated user.');
      }

      await user.sendEmailVerification();

      setState(() {
        _message = 'Verification email sent. Please check your inbox.';
      });
    } on FirebaseAuthException catch (e) {
      setState(() {
        _message = _mapFirebaseError(e);
      });
    } catch (_) {
      setState(() {
        _message = 'Failed to send verification email.';
      });
    } finally {
      setState(() {
        _isSending = false;
      });
    }
  }

  Future<void> _changeEmail(BuildContext context) async {
    await FirebaseAuth.instance.signOut();

    if (!mounted) return;

    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const SignupPage()),
      (route) => false,
    );
  }

  String _mapFirebaseError(FirebaseAuthException e) {
    switch (e.code) {
      case 'too-many-requests':
        return 'Too many requests. Please wait before retrying.';
      default:
        return 'Could not resend verification email.';
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.email_outlined, size: 64),

              const SizedBox(height: 24),

              const Text(
                'Verify your email',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 16),

              const Text(
                'We’ve sent a verification email to your inbox.\n'
                'Please check your email and follow the instructions to verify your account.',
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 24),

              if (_message != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    _message!,
                    style: const TextStyle(color: Colors.grey),
                    textAlign: TextAlign.center,
                  ),
                ),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSending ? null : _resendVerificationEmail,
                  child: _isSending
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Resend Verification Email'),
                ),
              ),
              const SizedBox(height: 12),

              TextButton(
                onPressed: () => _changeEmail(context),
                child: const Text('Change email address'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
