import Testing
import Combine
@testable import Aether

// MARK: - Registration ViewModel Tests

@MainActor
@Suite("RegistrationViewModel Tests")
struct RegistrationViewModelTests {

    // MARK: - Successful Registration Tests

    @Test("Registration with valid credentials succeeds")
    func registrationWithValidCredentials() async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        let expectedResponse = RegistrationResponse(
            id: UUID(),
            name: "testuser",
            email: "test@example.com",
            createdAt: Date()
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == true)
        #expect(sut.isLoading == false)
        #expect(sut.alertItem == nil)
    }

    @Test("Registration with password confirmation succeeds when passwords match")
    func registrationWithMatchingPasswordConfirmation() async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        let expectedResponse = RegistrationResponse(
            id: UUID(),
            name: "testuser",
            email: "test@example.com",
            createdAt: Date()
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Password123",
            confirmPassword: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == true)
        #expect(sut.alertItem == nil)
    }

    // MARK: - Username Validation Tests

    @Test("Registration with invalid username shows error",
          arguments: [
            "ab",           // Too short
            "a b",          // Contains space
            "test@user",    // Contains special char
            "te",           // Too short
            ""              // Empty
          ])
    func registrationWithInvalidUsername(invalidUsername: String) async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        // When
        await sut.register(
            username: invalidUsername,
            email: "test@example.com",
            password: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Invalid Username")
    }

    @Test("Registration with valid username formats succeeds",
          arguments: [
            "testuser",
            "test_user",
            "test123",
            "TEST_USER_123",
            "abc"
          ])
    func registrationWithValidUsername(validUsername: String) async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        let expectedResponse = RegistrationResponse(
            id: UUID(),
            name: validUsername,
            email: "test@example.com",
            createdAt: Date()
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.register(
            username: validUsername,
            email: "test@example.com",
            password: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == true)
        #expect(sut.alertItem == nil)
    }

    // MARK: - Email Validation Tests

    @Test("Registration with invalid email shows error",
          arguments: [
            "not-an-email",
            "test@",
            "@example.com",
            "test.example.com",
            "test @example.com",
            ""
          ])
    func registrationWithInvalidEmail(invalidEmail: String) async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        // When
        await sut.register(
            username: "testuser",
            email: invalidEmail,
            password: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Invalid Email")
    }

    // MARK: - Password Validation Tests

    @Test("Registration with short password shows error")
    func registrationWithShortPassword() async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Pass1" // Only 5 characters
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Password Too Short")
    }

    @Test("Registration with weak password shows error",
          arguments: [
            "password123",      // No uppercase
            "PASSWORD123",      // No lowercase
            "PasswordABC",      // No number
            "password",         // No uppercase or number
            "12345678"          // No letters
          ])
    func registrationWithWeakPassword(weakPassword: String) async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: weakPassword
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.alertItem != nil)
        // Should show either "Password Too Short" or "Weak Password"
        let isValidError = sut.alertItem?.title == "Weak Password" ||
                          sut.alertItem?.title == "Password Too Short"
        #expect(isValidError == true)
    }

    @Test("Registration with strong passwords succeeds",
          arguments: [
            "Password123",
            "StrongPass1",
            "MyP@ssw0rd",
            "Test1234",
            "Abcdefg1"
          ])
    func registrationWithStrongPassword(strongPassword: String) async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        let expectedResponse = RegistrationResponse(
            id: UUID(),
            name: "testuser",
            email: "test@example.com",
            createdAt: Date()
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: strongPassword
        )

        // Then
        #expect(registrationSuccessCalled == true)
        #expect(sut.alertItem == nil)
    }

    @Test("Registration with mismatched password confirmation shows error")
    func registrationWithMismatchedPasswordConfirmation() async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Password123",
            confirmPassword: "Password456" // Different
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Passwords Don't Match")
    }

    // MARK: - Network Error Tests

    @Test("Registration with network error shows alert")
    func registrationWithNetworkError() async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        mockNetwork.mockError = NetworkError.clientError("Email already exists")

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.isLoading == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Registration Failed")
        #expect(sut.alertItem?.message.contains("Email already exists") == true)
    }

    @Test("Registration with server error shows generic message")
    func registrationWithServerError() async {
        // Given
        let mockNetwork = MockNetworkService()
        var registrationSuccessCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { registrationSuccessCalled = true }
        )

        mockNetwork.mockError = NetworkError.serverError("Internal server error")

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Password123"
        )

        // Then
        #expect(registrationSuccessCalled == false)
        #expect(sut.alertItem != nil)
        #expect(sut.alertItem?.title == "Registration Failed")
    }

    // MARK: - Loading State Tests

    @Test("Registration sets and resets loading state")
    func registrationLoadingState() async {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        mockNetwork.latency = 0.05
        let expectedResponse = RegistrationResponse(
            id: UUID(),
            name: "testuser",
            email: "test@example.com",
            createdAt: Date()
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        let task = Task {
            await sut.register(
                username: "testuser",
                email: "test@example.com",
                password: "Password123"
            )
        }

        // Check loading during request
        try? await Task.sleep(for: .milliseconds(10))
        let isLoadingDuringRequest = sut.isLoading

        await task.value

        // Then
        #expect(isLoadingDuringRequest == true)
        #expect(sut.isLoading == false)
    }

    @Test("Registration clears previous alert on new attempt")
    func registrationClearsPreviousAlert() async {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        sut.alertItem = AlertItem(title: "Old Error", message: "Old message")

        let expectedResponse = RegistrationResponse(
            id: UUID(),
            name: "testuser",
            email: "test@example.com",
            createdAt: Date()
        )
        mockNetwork.mockResponse = expectedResponse

        // When
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "Password123"
        )

        // Then
        #expect(sut.alertItem == nil)
    }

    // MARK: - Navigation Tests

    @Test("Navigate to login calls callback")
    func navigateToLogin() {
        // Given
        let mockNetwork = MockNetworkService()
        var loginTappedCalled = false

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        sut.onLoginTapped = { loginTappedCalled = true }

        // When
        sut.navigateToLogin()

        // Then
        #expect(loginTappedCalled == true)
    }

    // MARK: - Initial State Tests

    @Test("Initial loading state is false")
    func initialLoadingState() {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        // Then
        #expect(sut.isLoading == false)
    }

    @Test("Initial alert is nil")
    func initialAlertState() {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        // Then
        #expect(sut.alertItem == nil)
    }

    // MARK: - Validation Priority Tests

    @Test("Validation checks username before email")
    func validationChecksUsernameFirst() async {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        // When - both username and email are invalid
        await sut.register(
            username: "ab", // Invalid username
            email: "invalid-email", // Invalid email
            password: "Password123"
        )

        // Then - should show username error first
        #expect(sut.alertItem?.title == "Invalid Username")
    }

    @Test("Validation checks email before password")
    func validationChecksEmailBeforePassword() async {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        // When - email is invalid, password is too short
        await sut.register(
            username: "testuser",
            email: "invalid-email", // Invalid email
            password: "Pass1" // Too short
        )

        // Then - should show email error first
        #expect(sut.alertItem?.title == "Invalid Email")
    }

    @Test("Validation checks password length before strength")
    func validationChecksPasswordLengthBeforeStrength() async {
        // Given
        let mockNetwork = MockNetworkService()

        let sut = RegistrationViewModelRefactored(
            network: mockNetwork,
            onRegisterSuccess: { }
        )

        // When - password is too short and weak
        await sut.register(
            username: "testuser",
            email: "test@example.com",
            password: "weak" // Too short and weak
        )

        // Then - should show length error first
        #expect(sut.alertItem?.title == "Password Too Short")
    }
}
