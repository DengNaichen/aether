import SwiftUI

struct AppCoordinatorView: View {
    
    @StateObject private var coordinator: AppCoordinator
    
    init(authService: AuthService, networkService: NetworkService) {
        self._coordinator = StateObject(wrappedValue: AppCoordinator(
            authService: authService,
            networkService: networkService))
    }
    
    var body: some View {
        Group {
            switch coordinator.state {
            case .checking:
                ProgressView("Checking Status ...")
                
            case .onboarding:
                if let onboardingCoordinator = coordinator.onboardingCoordinator {
                    OnboardingCoordinatorView(coordinator: onboardingCoordinator)
                }
                
            case .authenticated:
                if let mainCoordinator = coordinator.mainCoordinator {
                    MainCoordinatorView(coordinator: mainCoordinator)
                }
            }
        }
        .animation(.easeInOut, value: coordinator.state)
        .transition(.opacity)
    }
}
