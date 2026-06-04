import Foundation

struct APIClient {
    #if DEBUG
    static let baseURL = "http://localhost:8000"
    #else
    static let baseURL = ProcessInfo.processInfo.environment["BACKEND_URL"] ?? "http://localhost:8000"
    #endif

    private let token: String

    init(token: String) {
        self.token = token
    }

    func getTopics() async throws -> [Topic] {
        try await decode(get("/topics"))
    }

    func createTopic(phrase: String) async throws -> Topic {
        try await decode(post("/topics", body: ["phrase": phrase]))
    }

    func updateTopic(id: UUID, phrase: String? = nil, displayOrder: Int? = nil) async throws -> Topic {
        var body: [String: Any] = [:]
        if let phrase { body["phrase"] = phrase }
        if let displayOrder { body["display_order"] = displayOrder }
        return try await decode(patch("/topics/\(id.uuidString.lowercased())", body: body))
    }

    func deleteTopic(id: UUID) async throws {
        _ = try await delete("/topics/\(id.uuidString.lowercased())")
    }

    func updateSettings(deliveryTime: String) async throws {
        _ = try await patch("/settings", body: ["delivery_time": deliveryTime])
    }

    func getDigest() async throws -> Data {
        try await get("/digest")
    }

    func updateDeviceToken(_ token: String) async throws {
        _ = try await patch("/settings", body: ["device_token": token])
    }

    func generateDigest() async throws -> Digest {
        try await decode(post("/digest/generate", body: [:]))
    }

    func refreshCard(topicId: UUID) async throws -> TopicCard {
        try await decode(post("/digest/topics/\(topicId.uuidString.lowercased())/refresh", body: [:]))
    }

    // MARK: - Helpers

    private func decode<T: Decodable>(_ data: Data) throws -> T {
        try JSONDecoder().decode(T.self, from: data)
    }

    private func get(_ path: String) async throws -> Data {
        try await send(request(path, method: "GET"))
    }

    private func post(_ path: String, body: [String: Any]) async throws -> Data {
        var req = request(path, method: "POST")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await send(req)
    }

    private func patch(_ path: String, body: [String: Any]) async throws -> Data {
        var req = request(path, method: "PATCH")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await send(req)
    }

    private func delete(_ path: String) async throws -> Data {
        try await send(request(path, method: "DELETE"))
    }

    private func request(_ path: String, method: String) -> URLRequest {
        var req = URLRequest(url: URL(string: "\(Self.baseURL)\(path)")!)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        return req
    }

    private func send(_ req: URLRequest) async throws -> Data {
        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.httpError(0)
        }
        if http.statusCode == 429 {
            // Parse "Refresh available at HH:MM" from the FastAPI detail body.
            struct RateLimitBody: Decodable {
                struct Inner: Decodable { let detail: String }
                let detail: Inner
            }
            if let body = try? JSONDecoder().decode(RateLimitBody.self, from: data) {
                throw APIError.rateLimited(message: body.detail.detail)
            }
            throw APIError.rateLimited(message: "Try again in a moment")
        }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError.httpError(http.statusCode)
        }
        return data
    }

    enum APIError: LocalizedError {
        case httpError(Int)
        case rateLimited(message: String)
        var errorDescription: String? {
            switch self {
            case .httpError: return "Request failed. Please try again."
            case .rateLimited(let msg): return msg
            }
        }
    }
}
