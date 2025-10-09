import SwiftUI
//import SwiftData

@main
struct MaxwellApp: App {
    
    @StateObject private var authService: AuthService
    @StateObject private var networkService: NetworkService

    init() {
        let auth = AuthService()
        let ipAddress = "192.168.2.13"
        
        guard let baseURL = URL(string: "http://\(ipAddress):8000") else {
            fatalError("Invalid base URL provided.")
        }

        _authService = StateObject(wrappedValue: auth)
        _networkService = StateObject(wrappedValue: NetworkService(baseURL: baseURL, authService: auth))
    }
    
    var body: some Scene {
        WindowGroup {
            Group {
                if authService.isAuthenticated {
                    let enrollmentVM = EnrollmentViewModel(network: networkService)
                    WelcomeView(viewModel: enrollmentVM)
                } else {
                    let loginVM = LoginViewModel(network: networkService)
                    LoginView(viewModel: loginVM)
                }
            }
            .environmentObject(authService)
            .environmentObject(networkService)
            .task {
                await authService.checkAuthenticationStatus()
            }
        }
    }
}
