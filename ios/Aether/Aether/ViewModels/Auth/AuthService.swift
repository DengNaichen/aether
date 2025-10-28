import Foundation
import Combine
import KeychainAccess

// MARK: - Token Managing Protocol

/// Protocol for token management, allowing dependency injection and testing
protocol TokenManaging {
    /// Saves both access and refresh tokens securely
    func saveTokens(accessToken: String, refreshToken: String) async

    /// Retrieves the stored access token
    func getAccessToken() async -> String?

    /// Retrieves the stored refresh token
    func getRefreshToken() async -> String?

    /// Clears all stored tokens
    func clearToken() async
}

// MARK: - Token Manager Implementation

/// Concrete implementation of TokenManaging that stores tokens in the Keychain
///
/// This class uses a singleton pattern to ensure a single source of truth for tokens
/// across the application. It leverages the KeychainAccess library for secure storage.
/// NOTE: The tokenManager shouldn't be part of main actor
actor TokenManager: TokenManaging {
    static let shared = TokenManager()

    private let keychain = Keychain(service: Bundle.main.bundleIdentifier ?? "com.example.yourapp")

    private let accessTokenKey = "auth_access_token"
    private let refreshTokenKey = "auth_refresh_token"

    private init() {}
    
    /// Store `accessToken` and `refreshToken` into keychain
    func saveTokens(accessToken: String, refreshToken: String) {
        keychain[accessTokenKey] = accessToken
        keychain[refreshTokenKey] = refreshToken
    }
    
    /// Retrieves `AccessToken` from keychain
    func getAccessToken() -> String? {
        return keychain[accessTokenKey]
    }
    
    /// Retrieves `RefreshToken` from keychain
    func getRefreshToken() -> String? {
        return keychain[refreshTokenKey]
    }
    
    /// Clear all stored token
    func clearToken() {
        keychain[accessTokenKey] = nil
        keychain[refreshTokenKey] = nil
    }
}

/// A service class responsible for managing the authentication state and user session across the app.
///
/// `AuthService` keeps track of the current user's authentication token and user info.
/// It automatically notifies SwiftUI views when authentication data changes.
///
/// Features:
/// - Token-based authentication management
/// - Automatic token refresh handling
/// - User session management
/// - Observable state for SwiftUI integration
@MainActor
/// NOTE: HERE this is a main actor, as the auth service also a part of the
/// UI control, so it should be on the main actor
class AuthService: ObservableObject {

    // MARK: - Published Properties

    /// Indicates whether the user is currently authenticated
    @Published private(set) var isAuthenticated: Bool = false

    /// The currently authenticated user, if any
    @Published private(set) var currentUser: User?

    // MARK: - Private Properties

    private let tokenManager: TokenManaging

    // MARK: - Computed Properties

    /// Returns the current access token, if available
    var accessToken: String? {
        get async {
            await tokenManager.getAccessToken()
        }
    }

    // MARK: - Initialization

    /// Initializes the AuthService with a token manager
    /// - Parameter tokenManager: The token manager to use (defaults to shared instance)
    init(tokenManager: TokenManaging = TokenManager.shared) {
        self.tokenManager = tokenManager
        Task {
            await self.updateAuthenticationStatus()
        }
    }

    // MARK: - Public Methods

    /// Updates the authentication status based on the presence of a refresh token
    func updateAuthenticationStatus() async {
        isAuthenticated = await tokenManager.getRefreshToken() != nil
    }

    /// Sets the authenticated user and updates authentication status
    /// - Parameter user: The user to set as the current user
    func setCurrentUser(_ user: User) {
        self.currentUser = user
        self.isAuthenticated = true
    }

    /// Saves authentication tokens
    /// - Parameters:
    ///   - accessToken: The access token to save
    ///   - refreshToken: The refresh token to save
    func saveTokens(accessToken: String, refreshToken: String) async {
        await tokenManager.saveTokens(accessToken: accessToken, refreshToken: refreshToken)
        await updateAuthenticationStatus()
    }

    /// Refreshes access and refresh tokens using the stored refresh token
    ///
    /// - Parameter networkService: The network service to make the refresh request
    /// - Returns: `true` if refresh was successful, `false` if no refresh token available
    /// - Throws: NetworkError if the refresh request fails
    func refreshTokens(networkService: NetworkServicing) async throws -> Bool {
        // Check if we have a refresh token
        guard let currentRefreshToken = await tokenManager.getRefreshToken() else {
            print("⚠️ [AuthService] No refresh token available")
            await logout()
            return false
        }

        print("🔄 [AuthService] Refreshing tokens...")

        do {
            // Create refresh endpoint
            let endpoint = RefreshTokenEndpoint(refreshToken: currentRefreshToken)

            // Make the refresh request
            let response = try await networkService.request(
                endpoint: endpoint,
                responseType: TokenResponse.self
            )

            print("✅ [AuthService] Tokens refreshed successfully")

            // Debug: Log token preview before saving
            let newTokenPreview = String(response.accessToken.prefix(20))
            print("🔄 [AuthService] Saving new access token: \(newTokenPreview)...")

            // Save the new tokens
            await tokenManager.saveTokens(
                accessToken: response.accessToken,
                refreshToken: response.refreshToken
            )

            // Debug: Verify token was saved
            let savedToken = await tokenManager.getAccessToken()
            let savedTokenPreview = String(savedToken?.prefix(20) ?? "nil")
            print("✅ [AuthService] Token saved and verified: \(savedTokenPreview)...")

            await updateAuthenticationStatus()

            return true
        } catch {
            print("❌ [AuthService] Token refresh failed: \(error)")
            // Clear tokens on refresh failure to force re-authentication
            await logout()
            throw error
        }
    }

    /// Fetches the current user's information from the server
    /// - Parameter networkService: The network service to make the request
    /// - Throws: NetworkError if the request fails
    func fetchCurrentUser(networkService: NetworkServicing) async throws {
        let endpoint = GetUserInfoEndpoint()
        let user = try await networkService.request(
            endpoint: endpoint,
            responseType: User.self
        )
        self.currentUser = user
    }

    /// Logs out the current user and clears all authentication data
    func logout() async {
        await tokenManager.clearToken()
        isAuthenticated = false
        currentUser = nil
        print("🚪 [AuthService] User logged out")
    }
}
