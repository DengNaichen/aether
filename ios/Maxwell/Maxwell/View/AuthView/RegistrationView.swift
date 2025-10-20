import SwiftUI

struct RegisterView: View {
    @ObservedObject var viewModel: RegisterViewModel
    
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    
    
    private var isFormedValid: Bool {
        !name.isEmpty && email.contains("@") && password.count >= 6
    }

    init(viewModel: RegisterViewModel) {
        self.viewModel = viewModel
    }

    var body: some View {
        ZStack {
            NavigationStack {
                Form {
                    PersonalInfoSection(name: $name, email: $email)
                    PasswordSection(password: $password)
                    RegisterButtonSection(
                        text: "Register",
                        isEnable: !isFormedValid || viewModel.isLoading,
                        action: registerButtonTapped
                    )
                    LoginNavigationSection(
                        text: "Already have an account? Login",
                        action: viewModel.navigateToLogin)
                }
                .navigationTitle("Registration")
            }
            .disabled(viewModel.isLoading)
            
            if viewModel.isLoading {
                LoadingOverlay(message: "Registering...")
            }
        }
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(title: Text(alertItem.title),
                  message: Text(alertItem.message),
                  dismissButton: .default(Text("OK"))
            )
        }
    }
    private func registerButtonTapped() {
        Task {
            dismissKeyboard()
            await viewModel.register(username: name,
                                     email: email,
                                     password: password)
        }
    }
    
    private func dismissKeyboard() {
        UIApplication.shared.sendAction(
            #selector(UIResponder.resolveClassMethod(_:)),
            to: nil,
            from: nil,
            for: nil)
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
    return RegisterView(viewModel: mockViewModel)
}
