import SwiftUI

/// Coordinator for the 2-screen onboarding wizard (Add Topics → Delivery Time).
/// Shown only when a newly-signed-in user has zero topics.
struct OnboardingView: View {
    let token: String
    let onComplete: () -> Void

    @State private var step: Step = .topics
    @State private var addedTopics: [Topic] = []
    @State private var isGenerating = false
    @State private var generationError: String?

    private var api: APIClient { APIClient(token: token) }

    enum Step {
        case topics
        case deliveryTime
        case generating
    }

    var body: some View {
        NavigationStack {
            Group {
                switch step {
                case .topics:
                    OnboardingTopicsScreen(api: api) { topics in
                        addedTopics = topics
                        step = .deliveryTime
                    }

                case .deliveryTime:
                    OnboardingDeliveryScreen(api: api) {
                        step = .generating
                        generateDigest()
                    }

                case .generating:
                    generatingView
                }
            }
            .navigationBarBackButtonHidden(true)
            .toolbar {
                if step == .deliveryTime {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button {
                            step = .topics
                        } label: {
                            Image(systemName: "chevron.left")
                            Text("Back")
                        }
                    }
                }
            }
        }
    }

    // MARK: - Generating view

    private var generatingView: some View {
        VStack(spacing: 24) {
            Spacer()

            if let error = generationError {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundStyle(.orange)
                    Text("Something went wrong")
                        .font(.title2.bold())
                    Text(error)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                    Button("Retry") {
                        generationError = nil
                        generateDigest()
                    }
                    .buttonStyle(.borderedProminent)
                }
            } else {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Building your first digest…")
                        .font(.title2.bold())
                    Text("This may take a moment.")
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()
        }
        .padding(24)
    }

    // MARK: - Actions

    private func generateDigest() {
        isGenerating = true
        Task {
            do {
                _ = try await api.generateDigest()
                onComplete()
            } catch {
                generationError = "Failed to build your digest. Please try again."
                isGenerating = false
            }
        }
    }
}
