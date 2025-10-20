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
        _networkService = StateObject(
            wrappedValue: NetworkService(baseURL: baseURL, authService: auth))
    }
    
    var body: some Scene {
        WindowGroup {
            Group {
                if authService.isAuthenticated {
                    MainTabView(network: networkService)
                } else {
                    OnboardingFlow(network: networkService,
                                   authservice: authService)
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


struct OnboardingFlow: View {
    let network: NetworkService // TODO: don't know if this is right
    let authservice: AuthService
    
    @State private var showRegister = false
    
    var body: some View {
        if showRegister {
            RegisterView(viewModel: createRegisterViewModel())
        } else {
            LoginView(viewModel: createLoginViewModel())
        }
    }
    
    private func createLoginViewModel() -> LoginViewModel {
        let viewModel = LoginViewModel(network: network) {
            
        }
        viewModel.onRegisterTapped = {
            showRegister = true
        }
        return viewModel
    }
    
    private func createRegisterViewModel() -> RegisterViewModel {
        let viewModel = RegisterViewModel(network: network) {
            showRegister = false
        }
        viewModel.onLoginTapped = {
            showRegister = false
        }
        return viewModel
    }
}
