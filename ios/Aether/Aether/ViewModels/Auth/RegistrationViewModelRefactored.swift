import SwiftUI
import Foundation
import Combine

// MARK: - Registration Validation Errors
enum RegistrationValidationError {
    case invalidUsername
    case invalidEmail
    case weakPassword
    case passwordTooShort
    case passwordMismatch

    var title: String {
        switch self {
        case .invalidUsername:
            return "Invalid Username"
        case .invalidEmail:
            return "Invalid Email"
        case .weakPassword:
            return "Weak Password"
        case .passwordTooShort:
            return "Password Too Short"
        case .passwordMismatch:
            return "Passwords Don't Match"
        }
    }

    var message: String {
        switch self {
        case .invalidUsername:
            return "Username must be at least 3 characters and contain only letters, numbers, and underscores"
        case .invalidEmail:
            return "Please enter a valid email address"
        case .weakPassword:
            return "Password must contain at least one uppercase letter, one lowercase letter, and one number"
        case .passwordTooShort:
            return "Password must be at least 8 characters long"
        case .passwordMismatch:
            return "Password and confirmation password do not match"
        }
    }
}

// MARK: - Refactored Registration ViewModel
@MainActor
class RegistrationViewModelRefactored: ObservableObject {

    // MARK: - Dependencies
    private let network: NetworkServicing

    // MARK: - Published Properties
    @Published var isLoading: Bool = false
    @Published var alertItem: AlertItem?

    // MARK: - Callbacks
    var onRegisterSuccess: () -> Void
    var onLoginTapped: (() -> Void)?

    // MARK: - Initialization
    init(
        network: NetworkServicing,
        onRegisterSuccess: @escaping () -> Void
    ) {
        self.network = network
        self.onRegisterSuccess = onRegisterSuccess
    }

    // MARK: - Registration

    /// Registers a new user with the provided credentials
    /// - Parameters:
    ///   - username: The desired username
    ///   - email: The user's email address
    ///   - password: The user's password
    ///   - confirmPassword: Password confirmation (optional, for validation)
    func register(
        username: String,
        email: String,
        password: String,
        confirmPassword: String? = nil
    ) async {
        // Clear any previous alerts
        alertItem = nil

        // Validate inputs
        if let validationError = validateInputs(
            username: username,
            email: email,
            password: password,
            confirmPassword: confirmPassword
        ) {
            alertItem = AlertItem(
                title: validationError.title,
                message: validationError.message
            )
            return
        }

        // Perform registration
        await performRegistration(username: username, email: email, password: password)
    }

    // MARK: - Navigation

    /// Navigates to the login screen
    func navigateToLogin() {
        onLoginTapped?()
    }

    // MARK: - Private Helper Methods

    /// Performs the actual registration request
    private func performRegistration(username: String, email: String, password: String) async {
        isLoading = true
        defer { isLoading = false }

        do {
            let request = RegistrationRequest(
                name: username,
                email: email,
                password: password
            )

            let endpoint = RegisterEndpoint(registrationRequest: request)

            let _: RegistrationResponse = try await network.request(
                endpoint: endpoint,
                responseType: RegistrationResponse.self
            )

            // Notify success
            onRegisterSuccess()

        } catch {
            let errorMessage = parseError(error)
            alertItem = AlertItem(
                title: "Registration Failed",
                message: errorMessage
            )
        }
    }

    /// Validates all registration inputs
    /// - Returns: Validation error if any, nil if all inputs are valid
    private func validateInputs(
        username: String,
        email: String,
        password: String,
        confirmPassword: String?
    ) -> RegistrationValidationError? {
        // Validate username
        if !validateUsername(username) {
            return .invalidUsername
        }

        // Validate email
        if !validateEmail(email) {
            return .invalidEmail
        }

        // Validate password length
        if !validatePasswordLength(password) {
            return .passwordTooShort
        }

        // Validate password strength
        if !validatePasswordStrength(password) {
            return .weakPassword
        }

        // Validate password confirmation if provided
        if let confirmPassword = confirmPassword {
            if !validatePasswordMatch(password: password, confirmPassword: confirmPassword) {
                return .passwordMismatch
            }
        }

        return nil
    }

    /// Validates username format
    /// Username must be at least 3 characters and contain only letters, numbers, and underscores
    private func validateUsername(_ username: String) -> Bool {
        let usernameRegex = "^[a-zA-Z0-9_]{3,}$"
        let usernamePredicate = NSPredicate(format: "SELF MATCHES %@", usernameRegex)
        return usernamePredicate.evaluate(with: username)
    }

    /// Validates email format
    private func validateEmail(_ email: String) -> Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }

    /// Validates password length (minimum 8 characters)
    private func validatePasswordLength(_ password: String) -> Bool {
        return password.count >= 8
    }

    /// Validates password strength
    /// Password must contain at least one uppercase, one lowercase, and one number
    private func validatePasswordStrength(_ password: String) -> Bool {
        let uppercaseRegex = ".*[A-Z]+.*"
        let lowercaseRegex = ".*[a-z]+.*"
        let digitRegex = ".*[0-9]+.*"

        let uppercasePredicate = NSPredicate(format: "SELF MATCHES %@", uppercaseRegex)
        let lowercasePredicate = NSPredicate(format: "SELF MATCHES %@", lowercaseRegex)
        let digitPredicate = NSPredicate(format: "SELF MATCHES %@", digitRegex)

        return uppercasePredicate.evaluate(with: password) &&
               lowercasePredicate.evaluate(with: password) &&
               digitPredicate.evaluate(with: password)
    }

    /// Validates that password and confirmation match
    private func validatePasswordMatch(password: String, confirmPassword: String) -> Bool {
        return password == confirmPassword
    }

    /// Parses network error into user-friendly message
    private func parseError(_ error: Error) -> String {
        if let networkError = error as? NetworkError {
            return networkError.message
        }
        return "An unknown error occurred: \(error.localizedDescription)"
    }
}
