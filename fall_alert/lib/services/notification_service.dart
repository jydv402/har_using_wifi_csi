import 'package:firebase_messaging/firebase_messaging.dart';

class NotificationService {

  static Future<void> requestPermission() async {
    NotificationSettings settings =
        await FirebaseMessaging.instance.requestPermission();

    print("Notification permission: ${settings.authorizationStatus}");
  }

  static Future<String?> getFCMToken() async {
    String? token = await FirebaseMessaging.instance.getToken();
    print("FCM TOKEN: $token");
    return token;
  }
}
