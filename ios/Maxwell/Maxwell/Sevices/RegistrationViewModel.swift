import SwiftUI
import Foundation
import Combine


struct AlertItem: Identifiable {
    let id = UUID()
    let title: String
    let message: String
}

@MainActor
class RegistrationViewModel: ObservableObject {
    
    private let network: NetworkServicing

    @Published var isLoading: Bool = false
    @Published var registrationSuccessful: Bool = false
    @Published var alertItem: AlertItem?
    
    init(network: NetworkServicing) {
        self.network = network
    }
 
    func register(username: String, email: String, password: String) async {
        isLoading = true
        
        defer { isLoading = false }
//        errorMessage = nil
        registrationSuccessful = false
        
        let user = RegistrationRequest(name: username,
                                       email: email,
                                       password: password)
        do {
            let _: RegistrationResponse = try await network.request(
                endpoint: "/auth/register",
                method: .POST,
                body: .json(user),
                responseType: RegistrationResponse.self)
            print("Successfully Create User With Email \(user.email)")
            registrationSuccessful = true
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "An unknown error happen: \(error.localizedDescription)"
            }
            alertItem = AlertItem(title: "Registration Failed",
                                  message: errorMessage)
        }
    }
}
