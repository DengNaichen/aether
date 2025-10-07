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
    
    init() {
        print("➡️ [AuthService] Initializing...")
        
        if let _ = tokenManager.getRefreshToken() {
            print("✅ [AuthService] Found refresh token in Keychain.")
            isAuthenticated = true
        } else {
            print("🛑 [AuthService] No refresh token found in Keychain.")
            isAuthenticated = false
        }
    }

    func checkAuthenticationStatus() async {
        print("➡️ [AuthService] Checking authentication status...")
        if let _ = tokenManager.getRefreshToken() {
            print("✅ [AuthService] Found refresh token. User is authenticated.")
            self.isAuthenticated = true
        } else {
            print("🛑 [AuthService] No refresh token found. User is not authenticated.")
            self.isAuthenticated = false
        }
    }
    
    func logout() {
        tokenManager.clearToken()
        isAuthenticated = false
        currentUser = nil
        print("User logged out")
    }
}
