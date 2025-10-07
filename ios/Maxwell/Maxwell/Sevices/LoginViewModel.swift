import Foundation
import Combine


@MainActor
class LoginViewModel: ObservableObject {
    
    private let network: NetworkServicing
    
    @Published var isAuthenticated: Bool = false
    @Published var isLoading: Bool = false
    @Published var alartItem: AlertItem?
    
    init(network: NetworkServicing) {
        self.network = network
    }

    
    func login(email: String, password: String) async {
        isLoading = true
        defer { isLoading = false}
//        errorMessage = nil
        alartItem = nil
        
        let form_data = [
            "username": email,
            "password": password
        ]
//        LoginRequest(email: email, password: password)
        
        do {
            let tokenResponse: TokenResponse = try await network.request(
                endpoint: "/auth/login",
                method: .POST,
                body: .formUrlEncoded(form_data),
                responseType: TokenResponse.self
            )
            print("Successfully login, Token: \(tokenResponse.accessToken)")
            isAuthenticated = true
            
            self.isAuthenticated = true
            
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "unknown error happen: \(error.localizedDescription)"
            }
            self.alartItem = AlertItem(title: "Login Failed", message: errorMessage)
            self.isAuthenticated = false
        }
    }
}
