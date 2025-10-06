import Foundation
import Combine

/// A singleton class responsible for managing the authentication state and user session across the app.
///
/// `AuthenticationManager` keep track of the current user's authentication token and user info.
/// Automatically notify SwiftUI views when authentication data changes.
///  Use `AuthenticationManager.shared` to access the global instance.
@MainActor
class AuthenticationManager: ObservableObject {
    static let shared = AuthenticationManager()
    
    @Published private(set) var authToken: String?
    @Published private(set) var currentUser: User?
    
    var isAuthenticated: Bool {
        return authToken != nil && currentUser != nil
    }
    
    private init() {
        
    }
    
    func login(token: String, user: User) {
        self.authToken = token
        self.currentUser = user
        print("User \(user.name) login, the token has refreshed")
    }
    func logout() {
        self.authToken = nil
        self.currentUser = nil
        print("User logout")
    }
}
