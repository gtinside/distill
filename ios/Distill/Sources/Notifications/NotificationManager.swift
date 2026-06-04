import FirebaseMessaging
import UIKit
import UserNotifications

@MainActor
final class NotificationManager: NSObject, ObservableObject {
    static let shared = NotificationManager()

    func requestPermission() async {
        UNUserNotificationCenter.current().delegate = self
        try? await UNUserNotificationCenter.current().requestAuthorization(
            options: [.alert, .badge, .sound]
        )
        await UIApplication.shared.registerForRemoteNotifications()
    }

    func apnsTokenReceived(_ tokenData: Data) {
        Messaging.messaging().apnsToken = tokenData
    }

    func fcmTokenReceived(_ token: String) async {
        guard let sessionToken = try? await supabase.auth.session.accessToken else { return }
        let api = APIClient(token: sessionToken)
        try? await api.updateDeviceToken(token)
    }
}

extension NotificationManager: UNUserNotificationCenterDelegate {
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        NotificationCenter.default.post(name: .distillNavigateToDigest, object: nil)
        completionHandler()
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound, .badge])
    }
}

extension Notification.Name {
    static let distillNavigateToDigest = Notification.Name("distillNavigateToDigest")
}
