import Testing
import Combine
import AuthenticationServices
@testable import Aether

// MARK: - Login ViewModel Tests

@MainActor
@Suite("LoginViewModel Tests")
struct LoginViewModelTests {

    // MARK: - Email/Password Login Tests

    @Test("Login with valid credentials succeeds")
    func loginWithValidCredentials() async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()
        var loginSuccessCalled = false

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { loginSuccessCalled = true }
        )

        let expectedResponse = TokenResponse(
            accessToken: "access_token_123",
            refreshToken: "refresh_token_123",
            tokenType: "Bearer"
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.login(email: "test@example.com", password: "password123")

        // Then
        #expect(loginSuccessCalled == true)
        #expect(sut.isLoading == false)
        #expect(sut.alertItem == nil)
        #expect(mockAuth.savedAccessToken == "access_token_123")
        #expect(mockAuth.savedRefreshToken == "refresh_token_123")
    }

    @Test("Login with network error shows alert")
    func loginWithNetworkError() async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()
        var loginSuccessCalled = false

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { loginSuccessCalled = true }
        )

        mockNetwork.mockError = NetworkError.clientError("Invalid credentials")

        // When
        await sut.login(email: "test@example.com", password: "password123")

        // Then
        #expect(loginSuccessCalled == false)
        #expect(sut.isLoading == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Login Failed")
        #expect(sut.alertItem?.message.contains("Invalid credentials") == true)
    }

    @Test("Login with invalid email shows validation error",
          arguments: ["not-an-email", "test@", "@example.com", "test.example.com"])
    func loginWithInvalidEmail(invalidEmail: String) async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()
        var loginSuccessCalled = false

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { loginSuccessCalled = true }
        )

        // When
        await sut.login(email: invalidEmail, password: "password123")

        // Then
        #expect(loginSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Invalid Email")
    }

    @Test("Login with empty password shows validation error")
    func loginWithEmptyPassword() async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()
        var loginSuccessCalled = false

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { loginSuccessCalled = true }
        )

        // When
        await sut.login(email: "test@example.com", password: "")

        // Then
        #expect(loginSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Invalid Password")
    }

    @Test("Login sets and resets loading state")
    func loginLoadingState() async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { }
        )

        mockNetwork.latency = 0.05
        let expectedResponse = TokenResponse(
            accessToken: "token",
            refreshToken: "refresh",
            tokenType: "Bearer"
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        let task = Task {
            await sut.login(email: "test@example.com", password: "password123")
        }

        // Check loading during request
        try? await Task.sleep(for: .milliseconds(10))
        let isLoadingDuringRequest = sut.isLoading

        await task.value

        // Then
        #expect(isLoadingDuringRequest == true)
        #expect(sut.isLoading == false)
    }

    @Test("Login clears previous alert on new attempt")
    func loginClearsPreviousAlert() async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { }
        )

        sut.alertItem = AlertItem(title: "Old Error", message: "Old message")

        let expectedResponse = TokenResponse(
            accessToken: "token",
            refreshToken: "refresh",
            tokenType: "Bearer"
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.login(email: "test@example.com", password: "password123")

        // Then
        #expect(sut.alertItem == nil)
    }

    // MARK: - Google Sign-In Tests

    @Test("Google Sign-In with no view controller shows error")
    func googleSignInWithNoViewController() async {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()
        var loginSuccessCalled = false

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { nil }, // No view controller
            onLoginSuccess: { loginSuccessCalled = true }
        )

        // When
        await sut.handleGoogleSignIn()

        // Then
        #expect(loginSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Google Sign-In Failed")
        #expect(sut.alertItem?.message.contains("Unable to find") == true)
    }

    // MARK: - Navigation Tests

    @Test("Navigate to register calls callback")
    func navigateToRegister() {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()
        var registerCalled = false

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { }
        )

        sut.onRegisterTapped = { registerCalled = true }

        // When
        sut.navigateToRegister()

        // Then
        #expect(registerCalled == true)
    }

    // MARK: - Initial State Tests

    @Test("Initial loading state is false")
    func initialLoadingState() {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { }
        )

        // Then
        #expect(sut.isLoading == false)
    }

    @Test("Initial alert is nil")
    func initialAlertState() {
        // Given
        let mockNetwork = MockNetworkService()
        let mockAuth = MockAuthService()

        let sut = LoginViewModelRefactored(
            network: mockNetwork,
            authService: mockAuth,
            viewControllerProvider: { UIViewController() },
            onLoginSuccess: { }
        )

        // Then
        #expect(sut.alertItem == nil)
    }
}

// MARK: - Mock AuthService

@MainActor
final class MockAuthService: AuthService {
    var savedAccessToken: String?
    var savedRefreshToken: String?
    var saveTokensCalled = false

    init() {
        let mockTokenManager = MockTokenManager()
        super.init(tokenManager: mockTokenManager)
    }

    override func saveTokens(accessToken: String, refreshToken: String) {
        savedAccessToken = accessToken
        savedRefreshToken = refreshToken
        saveTokensCalled = true
        super.saveTokens(accessToken: accessToken, refreshToken: refreshToken)
    }
}

// MARK: - Mock TokenManager

@MainActor
final class MockTokenManager: TokenManaging {
    var accessToken: String?
    var refreshToken: String?

    func saveTokens(accessToken: String, refreshToken: String) {
        self.accessToken = accessToken
        self.refreshToken = refreshToken
    }

    func getAccessToken() -> String? {
        return accessToken
    }

    func getRefreshToken() -> String? {
        return refreshToken
    }

    func clearToken() {
        accessToken = nil
        refreshToken = nil
    }
}

// MARK: - Network Error Extension

extension NetworkError {
    var message: String {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .noData:
            return "No data received"
        case .decodingFailed:
            return "Failed to decode response"
        case .tokenNotFound:
            return "Authentication token not found"
        case .clientError(let message):
            return message
        case .serverError(let message):
            return message
        case .unknownError:
            return "Unknown error occurred"
        }
    }
}
