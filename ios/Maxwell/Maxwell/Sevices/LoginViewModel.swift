import Foundation
import Combine


@MainActor
class LoginViewModel: ObservableObject {
    
    private let network: NetworkServicing
    
    @Published var isAuthenticated: Bool = false
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    
    init(network: NetworkServicing) {
        self.network = network
    }

    
    func login(email: String, password: String) async {
        isLoading = true
        errorMessage = nil
        
        let credentials = LoginRequest(email: email, password: password)
        
        do {
            let tokenResponse: TokenResponse = try await network.request(
                endpoint: "/login",
                method: .POST,
                body: credentials,
                responseType: TokenResponse.self
            )
            print("Successfully login, Token: \(tokenResponse.accessToken)")
            isAuthenticated = true
            //                authService.login(credentials: request)
            
            
            await MainActor.run {
                self.isAuthenticated = true
            }
            
        } catch {
            if let networkError = error as? NetworkError {
                self.errorMessage = networkError.message
            } else {
                self.errorMessage = "unknown error happen: \(error.localizedDescription)"
            }
            self.isAuthenticated = false
        }
        isLoading = false
    }
}
