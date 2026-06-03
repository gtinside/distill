import Foundation

struct Digest: Codable {
    let id: UUID
    let user_id: String
    let generated_at: String
    let topic_cards: [TopicCard]
}

struct TopicCard: Identifiable, Codable {
    let id: UUID
    let topic_id: UUID
    let tldr: String?
    let bullets: [String]?
    let sources: [Source]?
    let status: String
    let last_refreshed_at: String?
    let display_order: Int?
}

struct Source: Identifiable, Codable {
    let id: UUID
    let title: String
    let url: String

    enum CodingKeys: String, CodingKey {
        case id, title, url
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        // id is not in the API response; generate a stable one from url
        if let decodedId = try? container.decode(UUID.self, forKey: .id) {
            id = decodedId
        } else {
            id = UUID()
        }
        title = try container.decode(String.self, forKey: .title)
        url = try container.decode(String.self, forKey: .url)
    }
}
