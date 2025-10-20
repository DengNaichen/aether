import SwiftUI


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
