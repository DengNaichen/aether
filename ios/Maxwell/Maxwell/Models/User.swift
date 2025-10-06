import Foundation

/// A simple model representing an authenticated user in the app.
struct User: Codable {
    let id: UUID
    let name: String
    let email: String
}


// after login, I hope to save the user's data and token for auto-login and show it on the welcome view. 
