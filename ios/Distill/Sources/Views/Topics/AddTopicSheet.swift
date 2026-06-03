import SwiftUI

private let suggestions = ["Fed policy", "Space exploration", "Premier League", "Watch releases"]

struct AddTopicSheet: View {
    @ObservedObject var viewModel: TopicsViewModel
    @Environment(\.dismiss) var dismiss
    @State private var phrase = ""
    @FocusState private var focused: Bool

    private var isValid: Bool { phrase.count >= 3 && phrase.count <= 60 }

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 20) {
                TextField("e.g. Fed policy", text: $phrase)
                    .focused($focused)
                    .textFieldStyle(.roundedBorder)
                    .submitLabel(.done)
                    .onSubmit { submit() }

                if phrase.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Suggestions")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                            ForEach(suggestions, id: \.self) { suggestion in
                                Button(suggestion) { phrase = suggestion }
                                    .buttonStyle(.bordered)
                                    .tint(.secondary)
                                    .frame(maxWidth: .infinity)
                            }
                        }
                    }
                }

                Spacer()
            }
            .padding()
            .navigationTitle("New Topic")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") { submit() }
                        .disabled(!isValid)
                }
            }
            .onAppear { focused = true }
        }
    }

    private func submit() {
        guard isValid else { return }
        Task {
            await viewModel.addTopic(phrase: phrase)
            dismiss()
        }
    }
}
