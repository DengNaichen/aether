import Foundation
import SwiftUI
import Combine

enum OnboardingState {
    case login
    case register
}

@MainActor
class OnboardingCoordinator: ObservableObject {
    @Published var state: OnboardingState = .login
    
    private let networkService: NetworkService
    var onFinish: () -> Void
    
    lazy var loginViewModel: LoginViewModel = {
        LoginViewModel(
            network: networkService,
            onLoginSuccess: { [weak self] in
                print("✅ OnboardingCoordinator: Login successful, calling onFinish.")
                self?.onFinish()
            }
        )
    }()
    
    lazy var registerViewModel: RegisterViewModel = {
        RegisterViewModel(
            network: networkService,
            onRegisterSuccess: { [weak self] in
                self?.onFinish()
            }
        )
    }()
    
    init(networkService: NetworkService, onFinish: @escaping () -> Void) {
        self.networkService = networkService
        self.onFinish = onFinish
        print("✅ OnboardingCoordinator initialized.")
    }
    
    deinit {
        print("🗑️ OnboardingCoordinator deinitialized.")
    }
    
    @ViewBuilder
    func start() -> some View {
        switch state {
        case .login:
            LoginView(viewModel: loginViewModel).environmentObject(self)
        case .register:
            RegisterView(viewModel: registerViewModel).environmentObject(self)
        }
    }
    
    func showRegisterView() {
        self.state = .register
    }
    
    func showLoginView() {
        self.state = .login
    }
}
