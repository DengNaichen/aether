import SwiftUI

struct RegisterView: View {
    @ObservedObject var viewModel: RegisterViewModel
    
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    
    private var isFormValid: Bool {
        !name.isEmpty && email.contains("@") && password.count >= 6
    }

    init(viewModel: RegisterViewModel) {
        self.viewModel = viewModel
    }

    var body: some View {
        ZStack {
            ScrollView {
                VStack(spacing: 24) {
                    AuthHeaderView(
                        title: "Create Account",
                        subtitle: "Start your personalized learning path today."
                    )
                    
                    VStack(spacing: 16) {
                        AuthTextField(placeholder: "Full Name", text: $name)
                        AuthTextField(placeholder: "Email", text: $email)
                        AuthTextField(placeholder: "Password", text: $password, isSecure: true)
                    }
                    
                    AuthButton(
                        title: "Sign Up",
                        action: registerButtonTapped,
                        isEnabled: isFormValid && !viewModel.isLoading
                    )
                    
                    OrDivider()
                    
                    VStack(spacing: 16) {
                        // Native Apple button
                        AppleSignInButtonView(title: "Sign up with Apple", action: {
                            // TODO: Implement Apple Sign-Up later
                        })
                        // Keep Google as your current custom button until SDK is added
                        GoogleSignInButtonView(action: {
                            // TODO: Implement Google Sign-Up later
                        })
                    }
                    
                    Spacer()
                    
                    AuthNavigationLink(
                        prompt: "Already have an account?",
                        actionText: "Login",
                        action: viewModel.navigateToLogin
                    )
                }
                .padding()
            }
            .navigationBarHidden(true)
            .disabled(viewModel.isLoading)
            
            if viewModel.isLoading {
                LoadingOverlay(message: "Registering...")
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
    
    private func registerButtonTapped() {
        Task {
            dismissKeyboard()
            await viewModel.register(username: name, email: email, password: password)
        }
    }
    
    private func dismissKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
}

// MARK: - Xcode preview
#Preview {
    let mockNet: NetworkServicing = MockNetworkService()
    let onSuccess: () -> Void = {
        print("Register success (preview)")
    }
    let mockViewModel = RegisterViewModel(
        network: mockNet,
        onRegisterSuccess: onSuccess
    )
    mockViewModel.onLoginTapped = {
        print("Navigate to login (preview)")
    }
    
    return NavigationView {
        RegisterView(viewModel: mockViewModel)
    }
}

