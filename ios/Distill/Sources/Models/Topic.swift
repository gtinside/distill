import Foundation

struct Topic: Identifiable, Codable, Equatable {
    let id: UUID
    let user_id: String
    let phrase: String
    var display_order: Int
}
