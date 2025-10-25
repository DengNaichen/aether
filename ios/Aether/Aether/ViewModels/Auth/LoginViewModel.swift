import Foundation
import Combine
import AuthenticationServices
import GoogleSignIn

@MainActor
class LoginViewModel: ObservableObject {
    
    private let network: NetworkServicing
    
    var onLoginSuccess: () -> Void
    var onRegisterTapped: (() -> Void)?

    @Published var isLoading: Bool = false
    @Published var alertItem: AlertItem?
    
    init(network: NetworkServicing, onLoginSuccess: @escaping () -> Void) {
        self.network = network
        self.onLoginSuccess = onLoginSuccess
    }
    
    func login(email: String, password: String) async {
        isLoading = true
        defer { isLoading = false }
        alertItem = nil
        
        let form_data = [
            "username": email,
            "password": password
        ]
        
        do {
            let tokenResponseEndpoint = LoginEndpoint(loginData: form_data)
            let tokenResponse: TokenResponse = try await network.request(endpoint: tokenResponseEndpoint, responseType: TokenResponse.self)
            print("Successfully login, Token: \(tokenResponse.accessToken)")
            
            TokenManager.shared.saveTokens(
                accessToken: tokenResponse.accessToken,
                refreshToken: tokenResponse.refreshToken
            )

            print("✅ [LoginViewModel] Tokens saved to Keychain.")
            self.onLoginSuccess()
            
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "unknown error happen: \(error.localizedDescription)"
            }
            self.alertItem = AlertItem(title: "Login Failed", message: errorMessage)
        }
    }
    
    func navigateToRegister() {
        onRegisterTapped?()
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
            
            // 获取用户信息
            let userID = appleIDCredential.user
            let email = appleIDCredential.email
            let fullName = appleIDCredential.fullName
            
            // 获取身份令牌
            guard let identityToken = appleIDCredential.identityToken,
                  let identityTokenString = String(data: identityToken, encoding: .utf8) else {
                alertItem = AlertItem(title: "Apple Sign-In Failed", message: "Failed to get identity token")
                return
            }
            
            // 发送到服务器验证
            await authenticateWithApple(
                userID: userID,
                identityToken: identityTokenString,
                email: email,
                fullName: fullName
            )
            
        case .failure(let error):
            if let authError = error as? ASAuthorizationError {
                switch authError.code {
                case .canceled:
                    // 用户取消登录，不显示错误
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
            } else {
                alertItem = AlertItem(title: "Apple Sign-In Failed", message: error.localizedDescription)
            }
        }
    }
    
    private func authenticateWithApple(
        userID: String,
        identityToken: String,
        email: String?,
        fullName: PersonNameComponents?
    ) async {
        do {
            // 创建Apple登录请求
            let appleRequest = AppleSignInRequest(
                userID: userID,
                identityToken: identityToken,
                email: email ?? "",
                firstName: fullName?.givenName ?? "",
                lastName: fullName?.familyName ?? ""
            )
            
            let endpoint = AppleSignInEndpoint(appleLoginRequest: appleRequest)
            let tokenResponse: TokenResponse = try await network.request(
                endpoint: endpoint, 
                responseType: TokenResponse.self
            )
            
            print("Successfully authenticated with Apple, Token: \(tokenResponse.accessToken)")
            
            TokenManager.shared.saveTokens(
                accessToken: tokenResponse.accessToken,
                refreshToken: tokenResponse.refreshToken
            )
            
            print("✅ [LoginViewModel] Apple Sign-In tokens saved to Keychain.")
            self.onLoginSuccess()
            
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "Apple Sign-In server error: \(error.localizedDescription)"
            }
            self.alertItem = AlertItem(title: "Apple Sign-In Failed", message: errorMessage)
        }
    }
    
    // MARK: - Google Sign-In
    func handleGoogleSignIn() async {
        isLoading = true
        defer { isLoading = false }
        alertItem = nil
        
        // 获取当前的根视图控制器
        guard let windowScene = await UIApplication.shared.connectedScenes
            .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene,
              let window = windowScene.windows.first(where: \.isKeyWindow),
              let presentingViewController = window.rootViewController else {
            alertItem = AlertItem(title: "Google Sign-In Failed", message: "Unable to find presenting view controller")
            return
        }
        
        do {
            let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: presentingViewController)
            let user = result.user
            
            // 获取用户信息
            let userID = user.userID ?? ""
            let email = user.profile?.email ?? ""
            let firstName = user.profile?.givenName ?? ""
            let lastName = user.profile?.familyName ?? ""
            
            // 获取ID Token
            guard let idToken = user.idToken?.tokenString else {
                alertItem = AlertItem(title: "Google Sign-In Failed", message: "Failed to get ID token")
                return
            }
            
            // 发送到服务器验证
            await authenticateWithGoogle(
                userID: userID,
                idToken: idToken,
                email: email,
                firstName: firstName,
                lastName: lastName
            )
            
        } catch {
            alertItem = AlertItem(title: "Google Sign-In Failed", message: error.localizedDescription)
        }
    }
    
    private func authenticateWithGoogle(
        userID: String,
        idToken: String,
        email: String,
        firstName: String,
        lastName: String
    ) async {
        do {
            // 创建Google登录请求
            let googleRequest = GoogleSignInRequest(
                userID: userID,
                idToken: idToken,
                email: email,
                firstName: firstName,
                lastName: lastName
            )
            
            let endpoint = GoogleSignInEndpoint(googleLoginRequest: googleRequest)
            let tokenResponse: TokenResponse = try await network.request(
                endpoint: endpoint,
                responseType: TokenResponse.self
            )
            
            print("Successfully authenticated with Google, Token: \(tokenResponse.accessToken)")
            
            TokenManager.shared.saveTokens(
                accessToken: tokenResponse.accessToken,
                refreshToken: tokenResponse.refreshToken
            )
            
            print("✅ [LoginViewModel] Google Sign-In tokens saved to Keychain.")
            self.onLoginSuccess()
            
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "Google Sign-In server error: \(error.localizedDescription)"
            }
            self.alertItem = AlertItem(title: "Google Sign-In Failed", message: errorMessage)
        }
    }
}
