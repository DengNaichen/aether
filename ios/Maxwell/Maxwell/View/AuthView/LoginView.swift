import SwiftUI

struct LoginView: View {
    // 视图持有并管理 ViewModel 的生命周期
    @ObservedObject var viewModel: LoginViewModel
    @EnvironmentObject var coordinator: OnboardingCoordinator
    
    
    // 用于UI输入的本地状态
    @State private var email = ""
    @State private var password = ""
    
    // TODO: I probably still need it
    init(viewModel: LoginViewModel) {
        self.viewModel = viewModel
    }

    var body: some View {
        ZStack {
            NavigationStack {
                Form {
                    Section(header: Text("邮箱")) {
                        TextField("输入邮箱", text: $email)
                            .keyboardType(.emailAddress)
                            .autocapitalization(.none)
                            .textContentType(.emailAddress) // 帮助iOS自动填充
                    }
                    
                    Section(header: Text("密码")) {
                        SecureField("输入密码", text: $password)
                            .textContentType(.password) // 帮助iOS自动填充
                    }
                    
                    Section {
                        Button(action: loginButtonTapped) {
                            HStack {
                                Spacer()
                                Text("登录")
                                Spacer()
                            }
                        }
                        .disabled(email.isEmpty || password.isEmpty || viewModel.isLoading)
                    }
                    Section {
                        // Using a Button with a custom style for navigation
                        Button(action: {
                            coordinator.showRegisterView()
                        }) {
                            Text("还没有账号？去注册")
                                .frame(maxWidth: .infinity, alignment: .center)
                        }
                    }
                }
                .navigationTitle("登录")
            }
            .disabled(viewModel.isLoading)
            
            // 根据 isLoading 状态显示加载动画
            if viewModel.isLoading {
                ProgressView("登录中...")
                    .progressViewStyle(CircularProgressViewStyle())
                    .padding()
                    .background(Color.secondary.colorInvert())
                    .cornerRadius(10)
                    .shadow(radius: 10)
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
