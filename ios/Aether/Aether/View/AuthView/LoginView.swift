import SwiftUI
import AuthenticationServices
import GoogleSignIn

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
                        // Apple Sign-In Button
                        SignInWithAppleButton(.signIn) { request in
                            request.requestedScopes = [.fullName, .email]
                        } onCompletion: { result in
                            Task {
                                await viewModel.handleAppleSignIn(result: result)
                            }
                        }
                        .signInWithAppleButtonStyle(.black)
                        .frame(height: 50)
                        .cornerRadius(10)
                        
                        // Google Sign-In Button
                        GoogleSignInButtonView(action: {
                            Task {
                                await viewModel.handleGoogleSignIn()
                            }
                        })
                        .disabled(viewModel.isLoading)
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
                LoadingOverlay(message: "Signing in...")
            }
        }
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(
                title: Text(alertItem.title),
                message: Text(alertItem.message),
                dismissButton: .default(Text("OK"))
            )
        }
        .onAppear {
            // 配置Google Sign-In
            configureGoogleSignIn()
        }
    }

    private func loginButtonTapped() {
        Task {
            await viewModel.login(email: email, password: password)
        }
    }
    
    private func configureGoogleSignIn() {
        // 这里需要配置Google Sign-In
        // 您需要在项目中添加GoogleService-Info.plist文件
        guard let path = Bundle.main.path(forResource: "GoogleService-Info", ofType: "plist"),
              let plist = NSDictionary(contentsOfFile: path),
              let clientID = plist["CLIENT_ID"] as? String else {
            print("⚠️ Google Sign-In configuration file not found")
            return
        }
        
        GIDSignIn.sharedInstance.configuration = GIDConfiguration(clientID: clientID)
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

