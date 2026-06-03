import SwiftUI

struct ContentView: View {
    @StateObject private var authManager = AuthManager()
    /// nil = still checking, false = show onboarding, true = show tab shell
    @State private var isOnboarded: Bool?

    var body: some View {
        Group {
            if authManager.session != nil {
                switch isOnboarded {
                case .none:
                    ProgressView()
                        .task { await checkOnboarded() }

                case .some(false):
                    onboardingView

                case .some(true):
                    tabShell
                }
            } else {
                SignInView()
                    .onAppear { isOnboarded = nil }
            }
        }
        .environmentObject(authManager)
        .animation(.default, value: authManager.session?.user.id)
        .onChange(of: authManager.session?.user.id) { _, _ in
            isOnboarded = nil
        }
    }

    // MARK: - Sub-views

    @ViewBuilder
    private var onboardingView: some View {
        // Use a task-based approach: fetch the token asynchronously inside OnboardingView
        OnboardingTokenView {
            isOnboarded = true
        }
    }

    private var tabShell: some View {
        TabView {
            DigestView()
                .tabItem { Label("Digest", systemImage: "newspaper") }
            TopicsView()
                .tabItem { Label("Topics", systemImage: "list.bullet") }
        }
    }

    // MARK: - Helpers

    private func checkOnboarded() async {
        guard let token = try? await supabase.auth.session.accessToken else { return }
        let api = APIClient(token: token)
        let count = (try? await api.getTopics().count) ?? 0
        isOnboarded = count > 0
    }
}

/// Resolves the auth token asynchronously, then hands off to OnboardingView.
private struct OnboardingTokenView: View {
    let onComplete: () -> Void
    @State private var token: String?

    var body: some View {
        Group {
            if let token {
                OnboardingView(token: token, onComplete: onComplete)
            } else {
                ProgressView()
            }
        }
        .task {
            token = try? await supabase.auth.session.accessToken
        }
    }
}
