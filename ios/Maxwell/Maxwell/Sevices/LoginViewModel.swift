import Foundation
import Combine

class LoginViewModel: ObservableObject {
    @Published var email: String = ""
    @Published var password: String = ""
    
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    
    @Published var isAuthenticated: Bool = false
    
    private let authService = AuthService()
    
    func login() {
        Task {
            isLoading = true
            errorMessage = nil
            
            let request = LoginRequest(email: email, password: password)
            
            do {
                let tokenResponse = try await authService.login(credentials: request)
                
                print("Successfully login, Token: \(tokenResponse.accessToken)")
                
                self.isAuthenticated = true
            } catch {
                if let authError = error as? AuthError {
                    switch authError {
                    case .invalidCredentials(let detail): self.errorMessage = detail
                    case .serverError(let detail): self.errorMessage = detail
                    default: self.errorMessage = "Unknown Error"
                    }
                } else {
                    self.errorMessage = error.localizedDescription
                }
            }
            isLoading = false
        }
    }
}
