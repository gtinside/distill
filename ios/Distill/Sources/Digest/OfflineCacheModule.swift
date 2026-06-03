import Foundation
import Network

// MARK: - Offline Cache

actor OfflineCacheModule {
    static let shared = OfflineCacheModule()

    private let fileURL: URL = {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return docs.appendingPathComponent("digest_cache.json")
    }()

    private struct CacheEnvelope: Codable {
        let digest: Digest
        let savedAt: Double
    }

    func save(_ digest: Digest, at date: Date) throws {
        let envelope = CacheEnvelope(digest: digest, savedAt: date.timeIntervalSince1970)
        let data = try JSONEncoder().encode(envelope)
        try data.write(to: fileURL, options: .atomic)
    }

    func load() throws -> (digest: Digest, savedAt: Date)? {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return nil }
        let data = try Data(contentsOf: fileURL)
        let envelope = try JSONDecoder().decode(CacheEnvelope.self, from: data)
        let date = Date(timeIntervalSince1970: envelope.savedAt)
        return (digest: envelope.digest, savedAt: date)
    }
}

// MARK: - Network Monitor

@MainActor
final class NetworkMonitor: ObservableObject {
    static let shared = NetworkMonitor()

    @Published var isOnline: Bool = true

    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.distill.NetworkMonitor")

    private init() {
        monitor.pathUpdateHandler = { [weak self] path in
            let online = path.status == .satisfied
            Task { @MainActor [weak self] in
                self?.isOnline = online
            }
        }
        monitor.start(queue: queue)
    }

    deinit {
        monitor.cancel()
    }
}
