import SwiftUI

private let suggestions = ["Fed policy", "Space exploration", "Premier League", "Watch releases"]

struct OnboardingTopicsScreen: View {
    let api: APIClient
    let onNext: ([Topic]) -> Void

    @State private var phrase = ""
    @State private var topics: [Topic] = []
    @State private var isAdding = false
    @State private var error: String?

    private var isValid: Bool { phrase.count >= 3 && phrase.count <= 60 }
    private var canProceed: Bool { !topics.isEmpty }

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            VStack(alignment: .leading, spacing: 6) {
                Text("What interests you?")
                    .font(.largeTitle.bold())
                Text("Add at least one topic to get your first digest.")
                    .foregroundStyle(.secondary)
            }

            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 10) {
                    TextField("e.g. Fed policy", text: $phrase)
                        .textFieldStyle(.roundedBorder)
                        .submitLabel(.done)
                        .onSubmit { addTopic() }

                    Button {
                        addTopic()
                    } label: {
                        if isAdding {
                            ProgressView().frame(width: 44, height: 36)
                        } else {
                            Text("Add")
                                .frame(width: 44, height: 36)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!isValid || isAdding)
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                    ForEach(suggestions, id: \.self) { suggestion in
                        let alreadyAdded = topics.contains { $0.phrase == suggestion }
                        Button {
                            if !alreadyAdded {
                                phrase = suggestion
                                addTopic()
                            }
                        } label: {
                            Text(suggestion)
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)
                        .tint(alreadyAdded ? .green : .secondary)
                        .disabled(alreadyAdded || isAdding)
                    }
                }
            }

            if !topics.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("\(topics.count) topic\(topics.count == 1 ? "" : "s") added")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    ForEach(topics) { topic in
                        Label(topic.phrase, systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                            .font(.subheadline)
                    }
                }
                .padding()
                .background(.green.opacity(0.08), in: RoundedRectangle(cornerRadius: 12))
            }

            if let error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            Spacer()

            Button {
                onNext(topics)
            } label: {
                Text("Next")
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 4)
            }
            .buttonStyle(.borderedProminent)
            .disabled(!canProceed)
        }
        .padding(24)
    }

    private func addTopic() {
        let trimmed = phrase.trimmingCharacters(in: .whitespaces)
        guard trimmed.count >= 3 && trimmed.count <= 60 else { return }
        isAdding = true
        error = nil
        Task {
            do {
                let topic = try await api.createTopic(phrase: trimmed)
                topics.append(topic)
                phrase = ""
            } catch {
                self.error = "Failed to add topic. Please try again."
            }
            isAdding = false
        }
    }
}
