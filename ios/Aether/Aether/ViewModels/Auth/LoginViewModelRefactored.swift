import Foundation
import Combine
import AuthenticationServices
import GoogleSignIn

// MARK: - Login Result
enum LoginResult {
    case success
    case failure(String)
}

// MARK: - Refactored LoginViewModel
@MainActor
class LoginViewModelRefactored: ObservableObject {

    // MARK: - Dependencies
    private let network: NetworkServicing
    private let authService: AuthService
    private let viewControllerProvider: () -> UIViewController?

    // MARK: - Published Properties
    @Published var isLoading: Bool = false
    @Published var alertItem: AlertItem?

    // MARK: - Callbacks
    var onLoginSuccess: () -> Void
    var onRegisterTapped: (() -> Void)?

    // MARK: - Initialization
    init(
        network: NetworkServicing,
        authService: AuthService,
        viewControllerProvider: @escaping () -> UIViewController? = { LoginViewModelRefactored.defaultViewControllerProvider() },
        onLoginSuccess: @escaping () -> Void
    ) {
        self.network = network
        self.authService = authService
        self.viewControllerProvider = viewControllerProvider
        self.onLoginSuccess = onLoginSuccess
    }

    // MARK: - Email/Password Login
    func login(email: String, password: String) async {
        // Validate input
        guard validateEmail(email) else {
            alertItem = AlertItem(title: "Invalid Email", message: "Please enter a valid email address")
            return
        }

        guard validatePassword(password) else {
            alertItem = AlertItem(title: "Invalid Password", message: "Password must not be empty")
            return
        }

        let formData = [
            "username": email,
            "password": password
        ]

        let endpoint = LoginEndpoint(loginData: formData)
        await performAuthentication(endpoint: endpoint)
    }

    // MARK: - Apple Sign-In
    func handleAppleSignIn(result: Result<ASAuthorization, Error>) async {
        isLoading = true
        defer { isLoading = false }
        alertItem = nil

        switch result {
        case .success(let authorization):
            guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential else {
                alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Invalid credentials received")
                return
            }

            guard let identityToken = appleIDCredential.identityToken,
                  let identityTokenString = String(data: identityToken, encoding: .utf8) else {
                alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Failed to get identity token")
                return
            }

            let request = AppleSignInRequest(
                userID: appleIDCredential.user,
                identityToken: identityTokenString,
                email: appleIDCredential.email ?? "",
                firstName: appleIDCredential.fullName?.givenName ?? "",
                lastName: appleIDCredential.fullName?.familyName ?? ""
            )

            let endpoint = AppleSignInEndpoint(appleLoginRequest: request)
            await performAuthentication(endpoint: endpoint)

        case .failure(let error):
            handleAppleSignInError(error)
        }
    }

    private func handleAppleSignInError(_ error: Error) {
        guard let authError = error as? ASAuthorizationError else {
            alertItem = AlertItem(title: "Apple Sign-In Failed", message: error.localizedDescription)
            return
        }

        switch authError.code {
        case .canceled:
            // User canceled, don't show error
            return
        case .unknown:
            alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Unknown error occurred")
        case .invalidResponse:
            alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Invalid response from Apple")
        case .notHandled:
            alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Sign in not handled")
        case .failed:
            alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Sign in failed")
        @unknown default:
            alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Unexpected error occurred")
        }
    }

    // MARK: - Google Sign-In
    func handleGoogleSignIn() async {
        isLoading = true
        defer { isLoading = false }
        alertItem = nil

        guard let presentingViewController = viewControllerProvider() else {
            alertItem = AlertItem(title: "Google Sign-In Failed", message: "Unable to find presenting view controller")
            return
        }

        do {
            let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presentingViewController)
            let user = result.user

            guard let idToken = user.idToken?.tokenString else {
                alertItem = AlertItem(title: "Google Sign-In Failed", message: "Failed to get ID token")
                return
            }

            let request = GoogleSignInRequest(
                userID: user.userID ?? "",
                idToken: idToken,
                email: user.profile?.email ?? "",
                firstName: user.profile?.givenName ?? "",
                lastName: user.profile?.familyName ?? ""
            )

            let endpoint = GoogleSignInEndpoint(googleLoginRequest: request)
            await performAuthentication(endpoint: endpoint)

        } catch {
            alertItem = AlertItem(title: "Google Sign-In Failed", message: error.localizedDescription)
        }
    }

    // MARK: - Navigation
    func navigateToRegister() {
        onRegisterTapped?()
    }

    // MARK: - Private Helper Methods

    /// Performs authentication with the given endpoint
    private func performAuthentication(endpoint: Endpoint) async {
        isLoading = true
        defer { isLoading = false }
        alertItem = nil

        do {
            let tokenResponse: TokenResponse = try await network.request(
                endpoint: endpoint,
                responseType: TokenResponse.self
            )

            // Save tokens through AuthService
            await authService.saveTokens(
                accessToken: tokenResponse.accessToken,
                refreshToken: tokenResponse.refreshToken
            )

            // Notify success
            onLoginSuccess()

        } catch {
            let errorMessage = parseError(error)
            alertItem = AlertItem(title: "Login Failed", message: errorMessage)
        }
    }

    /// Parses network error into user-friendly message
    private func parseError(_ error: Error) -> String {
        if let networkError = error as? NetworkError {
            return networkError.message
        }
        return "Unknown error: \(error.localizedDescription)"
    }

    /// Validates email format
    private func validateEmail(_ email: String) -> Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }

    /// Validates password (basic check)
    private func validatePassword(_ password: String) -> Bool {
        return !password.isEmpty
    }

    /// Default view controller provider
    @MainActor
    static func defaultViewControllerProvider() -> UIViewController? {
        guard let windowScene = UIApplication.shared.connectedScenes
            .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene,
              let window = windowScene.windows.first(where: \.isKeyWindow),
              let viewController = window.rootViewController else {
            return nil
        }
        return viewController
    }
}
