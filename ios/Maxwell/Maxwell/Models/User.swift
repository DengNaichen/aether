import Foundation

/// A simple model representing an authenticated user in the app.
struct User: Codable {
    let id: UUID
    let name: String
    let email: String
}
