import SwiftUI
import Foundation
import Combine


@MainActor
class RegistrationViewModel: ObservableObject {
    
    private let network: NetworkServicing

    @Published var isLoading: Bool = false
    @Published var registrationSuccessful: Bool = false
    @Published var errorMessage: String?
    
    init(network: NetworkServicing) {
        self.network = network
    }
 
    func register(username: String, email: String, password: String) async {
        isLoading = true
        errorMessage = nil
        registrationSuccessful = false
        
        let user = RegistrationRequest(name: username,
                                       email: email,
                                       password: password)
        do {
            let registrationResponse: RegistrationResponse = try await network.request(
                endpoint: "/registration",
                method: .POST,
                body: user,
                responseType: RegistrationResponse.self)
            print("Successfully Create User With Email \(user.email)")
            registrationSuccessful = true
        } catch {
            if let networkError = error as? NetworkError {
                self.errorMessage = networkError.message
            } else {
                self.errorMessage = "unknown error happen: \(error.localizedDescription)"
            }
        }
        isLoading = false
    }
}
