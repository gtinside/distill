import AuthenticationServices
import CryptoKit
import Supabase
import SwiftUI

@MainActor
final class AuthManager: ObservableObject {
    @Published var session: Session?
    private var rawNonce: String?

    init() {
        Task {
            session = try? await supabase.auth.session
            for await (_, newSession) in await supabase.auth.authStateChanges {
                session = newSession
            }
        }
    }

    // Returns the SHA256-hashed nonce to pass to Apple; stores the raw nonce for Supabase.
    func prepareSignIn() -> String {
        let nonce = randomNonce()
        rawNonce = nonce
        return sha256(nonce)
    }

    func handleSignInWithApple(_ authorization: ASAuthorization) async throws {
        guard
            let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
            let idTokenData = credential.identityToken,
            let idToken = String(data: idTokenData, encoding: .utf8),
            let nonce = rawNonce
        else { throw SignInError.invalidCredential }

        let session = try await supabase.auth.signInWithIdToken(credentials: .init(
            provider: .apple,
            idToken: idToken,
            nonce: nonce
        ))

        try await supabase.from("users")
            .upsert(UserRow(id: session.user.id, apple_sub: credential.user))
            .execute()
    }

    func signOut() async throws {
        try await supabase.auth.signOut()
    }

    private func randomNonce(length: Int = 32) -> String {
        let charset = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
        var result = ""
        var remaining = length
        while remaining > 0 {
            var bytes = [UInt8](repeating: 0, count: 16)
            SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes)
            for byte in bytes {
                if remaining == 0 { break }
                if byte < charset.count {
                    result.append(charset[Int(byte)])
                    remaining -= 1
                }
            }
        }
        return result
    }

    private func sha256(_ input: String) -> String {
        SHA256.hash(data: Data(input.utf8))
            .map { String(format: "%02x", $0) }
            .joined()
    }
}

extension AuthManager {
    enum SignInError: LocalizedError {
        case invalidCredential
        var errorDescription: String? { "Unable to complete sign in. Please try again." }
    }
}

private struct UserRow: Encodable {
    let id: UUID
    let apple_sub: String
}
