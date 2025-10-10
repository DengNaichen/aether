import SwiftUI
import Foundation
import Combine


struct AlertItem: Identifiable {
    let id = UUID()
    let title: String
    let message: String
}

@MainActor
class RegisterViewModel: ObservableObject {
    
    private let network: NetworkServicing
    var onRegisterSuccess: () -> Void

    @Published var isLoading: Bool = false
//    @Published var registrationSuccessful: Bool = false
    @Published var alertItem: AlertItem?
    
    init(network: NetworkServicing, onRegisterSuccess: @escaping () -> Void) {
        self.network = network
        self.onRegisterSuccess = onRegisterSuccess
    }
 
    func register(username: String, email: String, password: String) async {
        isLoading = true
        
        defer { isLoading = false }
//        registrationSuccessful = false
        
        do {
            let userRequest = RegistrationRequest(name: username,
                                                   email: email,
                                                   password: password)
            // create the endpoint
            let registerEndpoint = RegisterEndpoint(registrationRequest: userRequest)
            // get the response based on the endpoint
            // TODO: for the response, we can design more for further feature
            let _: RegistrationResponse = try await network.request(
                endpoint: registerEndpoint,
                responseType: RegistrationResponse.self
            )
            print("Successfully Create User With Email \(userRequest.email)")
//            registrationSuccessful = true
            onRegisterSuccess()
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
