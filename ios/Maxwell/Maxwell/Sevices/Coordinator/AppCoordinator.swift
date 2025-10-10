import SwiftUI
import Foundation
import Combine


enum AppState {
    case checking // checking the auth state
    case onboarding // need login or register
    case authenticated
}


@MainActor
class AppCoordinator: ObservableObject {
    @Published var state: AppState = .checking

    @Published var onboardingCoordinator: OnboardingCoordinator?
    @Published var mainCoordinator: MainCoordinator?
    
    private let authService: AuthService
    private var networkService: NetworkService
    private var cancellables = Set<AnyCancellable>()
    
    init(authService: AuthService, networkService: NetworkService) {
        self.networkService = networkService
        self.authService = authService
        authService.$isAuthenticated
            .sink { [weak self] isAuthenticated in
                print("Auth status changed to: \(isAuthenticated)")
                if isAuthenticated {
                    self?.showMainApp()
                } else {
                    self?.showOnboarding()
                }
            }
            .store(in: &cancellables)
        // << 临时的启动逻辑，强制显示登录页面 >>
        // 这会触发 authService.isAuthenticated = false (如果是初始状态)，
        // 进而触发上面的 sink，调用 showOnboarding()
        print("💡 [AppCoordinator] Using temporary startup logic: forcing onboarding state.")
        self.authService.isAuthenticated = false
    }
    
    func showOnboarding() {
        self.state = .onboarding
        self.mainCoordinator = nil
        self.onboardingCoordinator = OnboardingCoordinator(
            networkService: self.networkService,
            onFinish: { [weak self] in
//                self?.showMainApp()
                self?.authService.isAuthenticated = true
            }
        )
    }
    
    func showMainApp() {
        self.state = .authenticated
        self.onboardingCoordinator = nil
        self.mainCoordinator = MainCoordinator(
            networkService: self.networkService,
            onLogout: { [weak self] in
//                self?.showOnboarding()
                self?.authService.logout()
            }
        )
    }
}
