import AuthenticationServices
import SwiftUI

struct SignInView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var error: Error?

    var body: some View {
        VStack(spacing: 0) {
            Spacer()
            VStack(spacing: 12) {
                Image(systemName: "newspaper.fill")
                    .font(.system(size: 64))
                    .foregroundStyle(.primary)
                Text("Distill")
                    .font(.largeTitle.bold())
                Text("Your daily AI digest")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            SignInWithAppleButton(.signIn) { request in
                request.requestedScopes = [.fullName, .email]
                request.nonce = authManager.prepareSignIn()
            } onCompletion: { result in
                Task {
                    do {
                        switch result {
                        case .success(let auth): try await authManager.handleSignInWithApple(auth)
                        case .failure(let err): error = err
                        }
                    } catch {
                        self.error = error
                    }
                }
            }
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .padding(.horizontal, 40)
            .padding(.bottom, 60)
        }
        .alert(
            "Sign In Failed",
            isPresented: Binding(get: { error != nil }, set: { if !$0 { error = nil } })
        ) {
            Button("OK") { error = nil }
        } message: {
            Text(error?.localizedDescription ?? "An unexpected error occurred.")
        }
    }
}
