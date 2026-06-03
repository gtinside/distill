import Foundation
import Combine

@MainActor
final class DigestViewModel: ObservableObject {
    @Published var digest: Digest?
    @Published var isLoading = false
    @Published var error: Error?
    @Published var cacheDate: Date?
    @Published var isOffline: Bool = false

    private var api: APIClient?
    private var cancellables = Set<AnyCancellable>()

    func load(token: String) async {
        api = APIClient(token: token)

        // Observe network status
        NetworkMonitor.shared.$isOnline
            .receive(on: DispatchQueue.main)
            .sink { [weak self] online in
                self?.isOffline = !online
            }
            .store(in: &cancellables)

        await fetch()
    }

    func fetch() async {
        guard let api else { return }
        isLoading = true
        defer { isLoading = false }

        if !isOffline {
            // Online path: fetch from API
            do {
                let data = try await api.getDigest()
                let fetched = try JSONDecoder().decode(Digest.self, from: data)
                digest = fetched
                cacheDate = nil
                // Persist to cache
                let now = Date()
                try? await OfflineCacheModule.shared.save(fetched, at: now)
            } catch APIClient.APIError.httpError(404) {
                digest = nil
                cacheDate = nil
            } catch {
                self.error = error
                // Fall back to cache on network error
                await loadFromCache()
            }
        } else {
            // Offline path: serve from cache
            await loadFromCache()
        }
    }

    func updateCard(_ card: TopicCard) {
        guard var current = digest else { return }
        let updated = current.topic_cards.map { $0.id == card.id ? card : $0 }
        current = Digest(
            id: current.id,
            user_id: current.user_id,
            generated_at: current.generated_at,
            topic_cards: updated
        )
        digest = current
    }

    /// Refreshes a single TopicCard. Throws `APIClient.APIError.httpError(429)` on rate limit.
    func refreshCard(topicId: UUID) async throws -> TopicCard {
        guard let api else { throw APIClient.APIError.httpError(0) }
        return try await api.refreshCard(topicId: topicId)
    }

    // MARK: - Private

    private func loadFromCache() async {
        if let cached = try? await OfflineCacheModule.shared.load() {
            digest = cached.digest
            cacheDate = cached.savedAt
        }
    }
}
