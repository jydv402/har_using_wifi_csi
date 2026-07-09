import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../services/notification_service.dart';
import 'package:firebase_auth/firebase_auth.dart';

enum AppState { normal, fall, disconnected }

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  // ---------- CONFIG ----------
  //PC IP
  final String backendUrl = "https://fall-alert-backend-mdys.onrender.com";

  // ---------- STATE ----------
  AppState appState = AppState.normal;

  Timer? fallTimer;
  Timer? backendPollTimer;

  int secondsSinceFall = 0;

  late AnimationController rippleController;

  Future<void> initNotifications() async {
    await NotificationService.requestPermission();

    String? token = await NotificationService.getFCMToken();

    print("FCM TOKEN: $token");
  }

  // ---------- INIT ----------
  @override
  void initState() {
    super.initState();

    rippleController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1),
    );
    rippleController.repeat();
    initNotifications();
    startPollingBackend();
  }

  @override
  void dispose() {
    fallTimer?.cancel();
    backendPollTimer?.cancel();
    rippleController.dispose();
    super.dispose();
  }

  // ---------- BACKEND POLLING ----------

  void startPollingBackend() {
    backendPollTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      fetchBackendStatus();
    });
  }

  Future<void> fetchBackendStatus() async {
    try {
      final response = await http.get(Uri.parse("$backendUrl/status"));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data["status"] == "fall" && appState != AppState.fall) {
          triggerFall();
        }

        if (data["status"] == "normal" && appState != AppState.normal) {
          resetToNormal();
        }
      } else {
        setState(() {
          appState = AppState.disconnected;
        });
      }
    } catch (_) {
      setState(() {
        appState = AppState.disconnected;
      });
    }
  }

  // ---------- ACKNOWLEDGE ----------

  Future<void> acknowledgeFall() async {
    try {
      await http.post(Uri.parse("$backendUrl/acknowledge"));
    } catch (_) {}
  }

  // ---------- STATE LOGIC ----------

  void triggerFall() {
    setState(() {
      appState = AppState.fall;
      secondsSinceFall = 0;
    });

    rippleController.repeat();

    fallTimer?.cancel();
    fallTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        secondsSinceFall++;
      });
    });
  }

  void resetToNormal() {
    fallTimer?.cancel();
    rippleController.repeat();


    setState(() {
      appState = AppState.normal;
      secondsSinceFall = 0;
    });
  }

  Color getCircleColor() {
    switch (appState) {
      case AppState.normal:
        return Colors.green;
      case AppState.fall:
        return Colors.red;
      case AppState.disconnected:
        return Colors.yellow;
    }
  }

  // ---------- UI ----------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        title: const Text("Fall Alert"),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await FirebaseAuth.instance.signOut();
            },
          ),
        ],
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.only(top: 60, bottom: 30),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // MAIN CIRCLE
              // MAIN CIRCLE
              Stack(
                alignment: Alignment.center,
                children: [
                  // ---------- RIPPLE FOR FALL ----------
                  if (appState == AppState.fall)
                    AnimatedBuilder(
                      animation: rippleController,
                      builder: (context, child) {
                        double scale = 1 + rippleController.value * 0.6;

                        return Transform.scale(
                          scale: scale,
                          child: Container(
                            width: 300,
                            height: 300,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: Colors.red.withOpacity(
                                0.2 * (1 - rippleController.value),
                              ),
                            ),
                          ),
                        );
                      },
                    ),

                  // ---------- RIPPLE FOR NORMAL ----------
                  if (appState == AppState.normal)
                    AnimatedBuilder(
                      animation: rippleController,
                      builder: (context, child) {
                        double scale = 1 + rippleController.value * 0.4;

                        return Transform.scale(
                          scale: scale,
                          child: Container(
                            width: 300,
                            height: 300,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: Colors.green.withOpacity(
                                0.15 * (1 - rippleController.value),
                              ),
                            ),
                          ),
                        );
                      },
                    ),

                  // MAIN CIRCLE
                  Container(
                    width: 250,
                    height: 250,
                    decoration: BoxDecoration(
                      color: getCircleColor(),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Icon(
                        appState == AppState.fall
                            ? Icons.warning_rounded
                            : Icons.shield_rounded,
                        size: 90,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 30),

              //normal activity text
              if (appState == AppState.normal)
                const Text(
                  "Normal activity",
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                ),



              // FALL UI
              if (appState == AppState.fall) ...[
                Text(
                  "Fall occured: $secondsSinceFall s ago",
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 80),
                // ElevatedButton(
                //   onPressed: acknowledgeFall,
                //   child: const Text("OK"),
                // ),
                GestureDetector(
                  child: Container(
                    width: 200,
                    height: 50,

                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.shade400,
                          offset: Offset(4, 4),
                          blurRadius: 15,
                          spreadRadius: 1,
                        ),
                        BoxShadow(
                          color: Colors.white,
                          offset: Offset(-4, -4),
                          spreadRadius: 1,
                          blurRadius: 15,
                        ),
                      ],
                    ),
                    child: Center(
                      child: Text("Okay", style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
                    ),
                  ),
                  onTap: () {
                    acknowledgeFall();
                  },
                ),
              ],

              // DISCONNECTED UI
              if (appState == AppState.disconnected)
                const Text("Connection lost", style: TextStyle(fontSize: 18)),
            ],
          ),
        ),
      ),
    );
  }
}
