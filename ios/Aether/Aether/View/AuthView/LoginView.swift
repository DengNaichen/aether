import SwiftUI

struct LoginView: View {
    @ObservedObject var viewModel: LoginViewModel
    
    @State private var email = ""
    @State private var password = ""
    
    init(viewModel: LoginViewModel) {
        self.viewModel = viewModel
    }
    
    private var isFormValid: Bool {
        !email.isEmpty && email.contains("@") && !password.isEmpty
    }

    var body: some View {
        ZStack {
            ScrollView {
                VStack(spacing: 24) {
                    AuthHeaderView(
                        title: "Welcome Back!",
                        subtitle: "Sign in to continue your learning journey."
                    )
                    
                    VStack(spacing: 16) {
                        AuthTextField(placeholder: "Email", text: $email)
                        AuthTextField(placeholder: "Password", text: $password, isSecure: true)
                    }
                    
                    AuthButton(
                        title: "Login",
                        action: loginButtonTapped,
                        isEnabled: isFormValid && !viewModel.isLoading
                    )
                    
                    OrDivider()
                    
                    VStack(spacing: 16) {
                        // Native Apple button
                        AppleSignInButtonView(title: "Continue with Apple", action: {
                            // TODO: Implement Apple Sign-In later
                        })
                        // Keep Google as your current custom button until SDK is added
                        GoogleSignInButtonView(action: {
                            // TODO: Implement Google Sign-In later
                        })
                    }
                    
                    Spacer()
                    
                    AuthNavigationLink(
                        prompt: "Don't have an account?",
                        actionText: "Sign Up",
                        action: viewModel.navigateToRegister
                    )
                }
                .padding()
            }
            .navigationBarHidden(true)
            .disabled(viewModel.isLoading)
            
            if viewModel.isLoading {
                LoadingOverlay(message: "Logging in...")
            }
        }
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(
                title: Text(alertItem.title),
                message: Text(alertItem.message),
                dismissButton: .default(Text("OK"))
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
        print("Navigate to register (preview)")
    }
    
    return NavigationView {
        LoginView(viewModel: mockViewModel)
    }
}

