import SwiftUI
//import SwiftData

@main
struct MaxwellApp: App {
    
    @StateObject private var authService = AuthService()
    private var networkService: NetworkService

    init() {
        let ipAddress = "192.168.2.13"
        
        guard let baseURL = URL(string: "http://\(ipAddress):8000") else {
            fatalError("Invalid base URL provided.")
        }
        
        self.networkService = NetworkService(baseURL: baseURL)
    }
    
    var body: some Scene {
        WindowGroup {
            Group {
                if authService.isAuthenticated {
                    Text("登录成功！这里是主页面。")
                } else {
                    let loginViewModel = LoginViewModel(network: networkService)
                    LoginView(viewModel: loginViewModel)
                }
            }
            .environmentObject(authService)
            .task {
                await authService.checkAuthenticationStatus()
            }
        }
    }
}
