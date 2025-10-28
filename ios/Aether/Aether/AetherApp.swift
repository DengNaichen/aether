import SwiftUI
import SwiftData

@main
struct AetherApp: App {
    
    @StateObject private var authService: AuthService
    @State var networkService: NetworkService
    
    init() {
        let auth = AuthService()
        let testDevUrl = "https://aether-web-372668020909.northamerica-northeast2.run.app"
        
        guard let baseURL = URL(string: testDevUrl) else {
            fatalError("Invalid base URL provided.")
        }
        
        _authService = StateObject(wrappedValue: auth)
        _networkService = State(initialValue: NetworkService(baseURL: baseURL, authService: auth))
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
            .modelContainer(for: CourseModel.self)
        }
    }
}
