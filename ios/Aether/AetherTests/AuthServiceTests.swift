import Testing
import Foundation
@testable import Aether

/// Comprehensive test suite for AuthService
///
/// This test suite validates all authentication service functionality including:
/// - Token management
/// - Authentication status tracking
/// - User session management
/// - Token refresh flow
/// - Error handling
@MainActor
struct AuthServiceTests {

    // MARK: - Initialization Tests

    @Test func initializationWithNoTokensSetsUnauthenticated() async throws {
        // Given: A mock token manager with no tokens
        let mockTokenManager = MockTokenManager()

        // When: Initializing AuthService
        let authService = AuthService(tokenManager: mockTokenManager)

        // Then: Should be unauthenticated
        #expect(authService.isAuthenticated == false)
        #expect(authService.currentUser == nil)
        #expect(authService.accessToken == nil)
    }

    @Test func initializationWithRefreshTokenSetsAuthenticated() async throws {
        // Given: A mock token manager with a refresh token
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockRefreshToken = "valid-refresh-token"

        // When: Initializing AuthService
        let authService = AuthService(tokenManager: mockTokenManager)

        // Then: Should be authenticated
        #expect(authService.isAuthenticated == true)
    }

    @Test func initializationWithAccessTokenReturnsIt() async throws {
        // Given: A mock token manager with an access token
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockAccessToken = "valid-access-token"
        mockTokenManager.mockRefreshToken = "valid-refresh-token"

        // When: Initializing AuthService
        let authService = AuthService(tokenManager: mockTokenManager)

        // Then: Access token should be accessible
        #expect(authService.accessToken == "valid-access-token")
    }

    // MARK: - Authentication Status Update Tests

    @Test func updateAuthenticationStatusWithTokenSetsAuthenticated() async throws {
        // Given: An auth service and a token manager with no initial tokens
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        // When: Adding a refresh token and updating status
        mockTokenManager.mockRefreshToken = "new-refresh-token"
        authService.updateAuthenticationStatus()

        // Then: Should be authenticated
        #expect(authService.isAuthenticated == true)
    }

    @Test func updateAuthenticationStatusWithoutTokenSetsUnauthenticated() async throws {
        // Given: An auth service with initial token
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockRefreshToken = "initial-token"
        let authService = AuthService(tokenManager: mockTokenManager)

        // When: Removing the token and updating status
        mockTokenManager.mockRefreshToken = nil
        authService.updateAuthenticationStatus()

        // Then: Should be unauthenticated
        #expect(authService.isAuthenticated == false)
    }

    // MARK: - User Management Tests

    @Test func setCurrentUserSetsUserAndAuthenticated() async throws {
        // Given: An unauthenticated auth service
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        // When: Setting a current user
        let user = User(id: UUID(), name: "Test User", email: "test@example.com")
        authService.setCurrentUser(user)

        // Then: User should be set and authenticated
        #expect(authService.currentUser?.id == user.id)
        #expect(authService.currentUser?.name == "Test User")
        #expect(authService.currentUser?.email == "test@example.com")
        #expect(authService.isAuthenticated == true)
    }

    // MARK: - Token Saving Tests

    @Test func saveTokensStoresTokensAndUpdatesStatus() async throws {
        // Given: An auth service
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        // When: Saving tokens
        authService.saveTokens(accessToken: "new-access", refreshToken: "new-refresh")

        // Then: Tokens should be saved and authenticated
        #expect(mockTokenManager.savedAccessToken == "new-access")
        #expect(mockTokenManager.savedRefreshToken == "new-refresh")
        #expect(authService.isAuthenticated == true)
    }

    // MARK: - Token Refresh Tests

    @Test func refreshTokensSucceedsWithValidRefreshToken() async throws {
        // Given: An auth service with a refresh token
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockRefreshToken = "old-refresh-token"
        mockTokenManager.mockAccessToken = "old-access-token"
        let authService = AuthService(tokenManager: mockTokenManager)

        // And: A test network service that returns new tokens
        let testNetworkService = TestNetworkService()
        testNetworkService.mockResponse = TokenResponse(
            accessToken: "new-access-token",
            refreshToken: "new-refresh-token",
            tokenType: "bearer"
        )

        // When: Refreshing tokens
        let result = try await authService.refreshTokens(networkService: testNetworkService)

        // Then: Should succeed and save new tokens
        #expect(result == true)
        #expect(mockTokenManager.savedAccessToken == "new-access-token")
        #expect(mockTokenManager.savedRefreshToken == "new-refresh-token")
        #expect(authService.isAuthenticated == true)
    }

    @Test func refreshTokensFailsWithoutRefreshToken() async throws {
        // Given: An auth service without a refresh token
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        let testNetworkService = TestNetworkService()

        // When: Attempting to refresh tokens
        let result = try await authService.refreshTokens(networkService: testNetworkService)

        // Then: Should fail and logout
        #expect(result == false)
        #expect(authService.isAuthenticated == false)
        #expect(authService.currentUser == nil)
    }

    @Test func refreshTokensLogsOutOnNetworkError() async throws {
        // Given: An auth service with a refresh token
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockRefreshToken = "refresh-token"
        mockTokenManager.mockAccessToken = "access-token"
        let authService = AuthService(tokenManager: mockTokenManager)

        // And: A test network service that throws an error
        let testNetworkService = TestNetworkService()
        testNetworkService.mockError = TestNetworkError.unauthorized

        // When/Then: Refreshing should throw an error
        await #expect(throws: Error.self) {
            try await authService.refreshTokens(networkService: testNetworkService)
        }

        // And: Should logout the user
        #expect(authService.isAuthenticated == false)
        #expect(authService.currentUser == nil)
        #expect(mockTokenManager.clearTokenCalled == true)
    }

    @Test func refreshTokensUpdatesAuthenticationStatus() async throws {
        // Given: An auth service with tokens
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockRefreshToken = "old-refresh"
        let authService = AuthService(tokenManager: mockTokenManager)

        // And: A successful network response
        let testNetworkService = TestNetworkService()
        testNetworkService.mockResponse = TokenResponse(
            accessToken: "new-access",
            refreshToken: "new-refresh",
            tokenType: "bearer"
        )

        // When: Refreshing tokens
        _ = try await authService.refreshTokens(networkService: testNetworkService)

        // Then: Authentication status should be updated
        #expect(authService.isAuthenticated == true)
    }

    // MARK: - Fetch Current User Tests

    @Test func fetchCurrentUserSetsCurrentUser() async throws {
        // Given: An auth service
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        // And: A test network service that returns user info
        let testNetworkService = TestNetworkService()
        let expectedUser = User(
            id: UUID(),
            name: "John Doe",
            email: "john@example.com"
        )
        testNetworkService.mockResponse = expectedUser

        // When: Fetching current user
        try await authService.fetchCurrentUser(networkService: testNetworkService)

        // Then: Current user should be set
        #expect(authService.currentUser?.id == expectedUser.id)
        #expect(authService.currentUser?.name == "John Doe")
        #expect(authService.currentUser?.email == "john@example.com")
    }

    @Test func fetchCurrentUserThrowsOnNetworkError() async throws {
        // Given: An auth service
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        // And: A test network service that throws an error
        let testNetworkService = TestNetworkService()
        testNetworkService.mockError = TestNetworkError.serverError

        // When/Then: Fetching should throw an error
        await #expect(throws: Error.self) {
            try await authService.fetchCurrentUser(networkService: testNetworkService)
        }

        // And: Current user should remain nil
        #expect(authService.currentUser == nil)
    }

    // MARK: - Logout Tests

    @Test func logoutClearsAllAuthenticationData() async throws {
        // Given: An authenticated auth service with user
        let mockTokenManager = MockTokenManager()
        mockTokenManager.mockRefreshToken = "refresh-token"
        mockTokenManager.mockAccessToken = "access-token"
        let authService = AuthService(tokenManager: mockTokenManager)

        let user = User(id: UUID(), name: "Test User", email: "test@example.com")
        authService.setCurrentUser(user)

        // When: Logging out
        authService.logout()

        // Then: All authentication data should be cleared
        #expect(authService.isAuthenticated == false)
        #expect(authService.currentUser == nil)
        #expect(mockTokenManager.clearTokenCalled == true)
    }

    @Test func logoutCanBeCalledMultipleTimes() async throws {
        // Given: An auth service
        let mockTokenManager = MockTokenManager()
        let authService = AuthService(tokenManager: mockTokenManager)

        // When: Logging out multiple times
        authService.logout()
        authService.logout()
        authService.logout()

        // Then: Should not crash and remain unauthenticated
        #expect(authService.isAuthenticated == false)
        #expect(authService.currentUser == nil)
    }
}

// MARK: - Mock Token Manager

@MainActor
class MockTokenManager: TokenManaging {
    var mockAccessToken: String?
    var mockRefreshToken: String?

    var savedAccessToken: String?
    var savedRefreshToken: String?
    var clearTokenCalled = false

    func saveTokens(accessToken: String, refreshToken: String) {
        savedAccessToken = accessToken
        savedRefreshToken = refreshToken
        mockAccessToken = accessToken
        mockRefreshToken = refreshToken
    }

    func getAccessToken() -> String? {
        return mockAccessToken
    }

    func getRefreshToken() -> String? {
        return mockRefreshToken
    }

    func clearToken() {
        mockAccessToken = nil
        mockRefreshToken = nil
        savedAccessToken = nil
        savedRefreshToken = nil
        clearTokenCalled = true
    }
}

// MARK: - Test Network Service
// Note: This is separate from the main app's MockNetworkService which is used for previews
// This one is designed specifically for unit testing with tracking capabilities

@MainActor
class TestNetworkService: NetworkServicing {
    var mockResponse: Any?
    var mockError: Error?
    var requestedEndpoints: [Endpoint] = []

    func request<T: Decodable>(endpoint: Endpoint, responseType: T.Type) async throws -> T {
        requestedEndpoints.append(endpoint)

        if let error = mockError {
            throw error
        }

        guard let response = mockResponse as? T else {
            throw TestNetworkError.invalidResponse
        }

        return response
    }
}

// MARK: - Test Network Error

enum TestNetworkError: Error {
    case unauthorized
    case serverError
    case invalidResponse
    case generalError
}
