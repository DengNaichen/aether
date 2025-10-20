import Foundation
import Combine

/// A singleton class responsible for managing the authentication state and user session across the app.
///
/// `AuthenticationManager` keep track of the current user's authentication token and user info.
/// Automatically notify SwiftUI views when authentication data changes.
///  Use `AuthenticationManager.shared` to access the global instance.
@MainActor
class AuthService: ObservableObject {
    
    @Published var isAuthenticated: Bool = false
    @Published var currentUser: User?
    
    private let tokenManager = TokenManager.shared
    
    var accessToken: String? {
        let token = tokenManager.getAccessToken()
        return token
    }
    
    init() {
        if let _ = tokenManager.getRefreshToken() {
            isAuthenticated = true
        } else {
            isAuthenticated = false
        }
    }

    func checkAuthenticationStatus() async {
        if let _ = tokenManager.getRefreshToken() {
            self.isAuthenticated = true
        } else {
            self.isAuthenticated = false
        }
    }
    
    func logout() {
        tokenManager.clearToken()
        isAuthenticated = false
        currentUser = nil
    }
}
