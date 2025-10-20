import SwiftUI

struct LoginView: View {
    @ObservedObject var viewModel: LoginViewModel
    
    @State private var email = ""
    @State private var password = ""
    
    init(viewModel: LoginViewModel) {
        self.viewModel = viewModel
    }

    var body: some View {
        ZStack {
            NavigationStack {
                Form {
                    LoginInfoSection(email: $email)
                    PasswordSection(password: $password)
                    RegisterButtonSection(
                        text: "Login",
                        isEnable: email.isEmpty || password.isEmpty ||
                        viewModel.isLoading,
                        action: loginButtonTapped
                    )
                    Section {
                        // Using a Button with a custom style for navigation
                        Button(action: {
                            viewModel.navigateToRegister()
                        }) {
                            Text("No account? Sign up")
                                .frame(maxWidth: .infinity, alignment: .center)
                        }
                    }
//                    LoginNavigationSection(
//                        text: "No account? Sign up",
//                        action: viewModel.navigateToRegister()
//                    )
                }
                .navigationTitle("Login")
            }
            .disabled(viewModel.isLoading)
            
            // 根据 isLoading 状态显示加载动画
            if viewModel.isLoading {
                LoadingOverlay(message: "Login...")
            }
        }
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(
                title: Text(alertItem.title),
                message: Text(alertItem.message),
                dismissButton: .default(Text("Ok"))
            )
        }
    }

    private func loginButtonTapped() {
        Task {
            await viewModel.login(email: email, password: password)
        }
    }
}

// MARK: - Xcode Preview
#Preview {
    let mockNet: NetworkServicing = MockNetworkService()
    let onSuccess: () -> Void = {
        print("Login success (preview)")
    }
    let mockViewModel = LoginViewModel(network: mockNet, onLoginSuccess: onSuccess)
    mockViewModel.onRegisterTapped = {
        print("Navigate to register(preview)")
    }
    return LoginView(viewModel: mockViewModel)
}
