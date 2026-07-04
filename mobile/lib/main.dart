import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // No FirebaseOptions passed - on Android this reads configuration from
  // android/app/google-services.json automatically at build time.
  await Firebase.initializeApp();
  runApp(const LandDisputeCitizenApp());
}

class LandDisputeCitizenApp extends StatelessWidget {
  const LandDisputeCitizenApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Land Dispute Citizen',
      theme: buildAppTheme(),
      debugShowCheckedModeBanner: false,
      home: const SplashScreen(),
    );
  }
}
