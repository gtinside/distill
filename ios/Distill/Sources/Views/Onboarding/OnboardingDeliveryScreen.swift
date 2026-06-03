import SwiftUI

struct OnboardingDeliveryScreen: View {
    let api: APIClient
    let onDone: () -> Void

    @State private var deliveryTime: Date = defaultDeliveryTime()
    @State private var isSaving = false
    @State private var error: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            VStack(alignment: .leading, spacing: 6) {
                Text("When should we deliver?")
                    .font(.largeTitle.bold())
                Text("Pick a daily delivery time for your digest. You can change this later.")
                    .foregroundStyle(.secondary)
            }

            DatePicker(
                "Delivery time",
                selection: $deliveryTime,
                displayedComponents: .hourAndMinute
            )
            .datePickerStyle(.wheel)
            .labelsHidden()
            .frame(maxWidth: .infinity)

            if let error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            Spacer()

            Button {
                save()
            } label: {
                if isSaving {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 4)
                } else {
                    Text("Done")
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 4)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(isSaving)
        }
        .padding(24)
    }

    private func save() {
        isSaving = true
        error = nil
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        let timeString = formatter.string(from: deliveryTime)
        Task {
            do {
                try await api.updateSettings(deliveryTime: timeString)
                onDone()
            } catch {
                self.error = "Failed to save delivery time. Please try again."
                isSaving = false
            }
        }
    }
}

private func defaultDeliveryTime() -> Date {
    Calendar.current.date(from: DateComponents(hour: 7, minute: 0)) ?? Date()
}
