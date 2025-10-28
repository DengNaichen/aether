import SwiftUI


struct OnboardingFlow: View {
    let network: NetworkServicing
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
            // 登录成功后更新认证状态
            Task {
                await authservice.updateAuthenticationStatus()
            }
        }
        viewModel.onRegisterTapped = {
            showRegister = true
        }
        return viewModel
    }

    private func createRegisterViewModel() -> RegisterViewModel {
        let viewModel = RegisterViewModel(network: network) {
            // 注册成功后切换回登录界面
            showRegister = false
        }
        viewModel.onLoginTapped = {
            showRegister = false
        }
        return viewModel
    }
}
