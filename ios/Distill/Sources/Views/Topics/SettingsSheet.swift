import SwiftUI

struct SettingsSheet: View {
    @ObservedObject var viewModel: TopicsViewModel
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) var dismiss
    @State private var deliveryTime: Date = defaultDeliveryTime()

    var body: some View {
        NavigationStack {
            Form {
                Section("Digest Delivery") {
                    DatePicker("Time", selection: $deliveryTime, displayedComponents: .hourAndMinute)
                }
                Section {
                    Button("Sign Out", role: .destructive) {
                        Task { try? await authManager.signOut() }
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await viewModel.updateDeliveryTime(deliveryTime)
                            dismiss()
                        }
                    }
                }
            }
        }
        .task {
            if let date = await viewModel.fetchDeliveryTime() {
                deliveryTime = date
            }
        }
    }
}

private func defaultDeliveryTime() -> Date {
    Calendar.current.date(from: DateComponents(hour: 7, minute: 0)) ?? Date()
}
