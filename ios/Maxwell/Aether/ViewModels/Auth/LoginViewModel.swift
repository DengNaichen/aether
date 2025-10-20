import Foundation
import Combine


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
}
