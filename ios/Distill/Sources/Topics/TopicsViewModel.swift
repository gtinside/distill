import Foundation
import Supabase

@MainActor
final class TopicsViewModel: ObservableObject {
    @Published var topics: [Topic] = []
    @Published var isLoading = false
    @Published var error: Error?

    private var api: APIClient?

    func load(token: String) async {
        api = APIClient(token: token)
        await refresh()
    }

    func refresh() async {
        guard let api else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            topics = try await api.getTopics()
        } catch {
            self.error = error
        }
    }

    func addTopic(phrase: String) async {
        guard let api else { return }
        do {
            let topic = try await api.createTopic(phrase: phrase)
            topics.append(topic)
        } catch {
            self.error = error
        }
    }

    func delete(at offsets: IndexSet) async {
        let ids = offsets.map { topics[$0].id }
        topics.remove(atOffsets: offsets)
        guard let api else { return }
        for id in ids {
            try? await api.deleteTopic(id: id)
        }
    }

    func move(from source: IndexSet, to destination: Int) async {
        topics.move(fromOffsets: source, toOffset: destination)
        guard let api else { return }
        await withTaskGroup(of: Void.self) { group in
            for (index, topic) in topics.enumerated() {
                group.addTask {
                    _ = try? await api.updateTopic(id: topic.id, displayOrder: index)
                }
            }
        }
    }

    func updateDeliveryTime(_ date: Date) async {
        guard let api else { return }
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        do {
            try await api.updateSettings(deliveryTime: formatter.string(from: date))
        } catch {
            self.error = error
        }
    }

    func fetchDeliveryTime() async -> Date? {
        guard let session = try? await supabase.auth.session else { return nil }
        let profiles: [UserProfile] = (try? await supabase
            .from("users")
            .select("delivery_time")
            .eq("id", value: session.user.id.uuidString)
            .execute()
            .value) ?? []
        guard let raw = profiles.first?.delivery_time else { return nil }
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        return formatter.date(from: raw)
    }

    var canAddTopic: Bool { topics.count < 10 }
}

private struct UserProfile: Decodable {
    let delivery_time: String
}
