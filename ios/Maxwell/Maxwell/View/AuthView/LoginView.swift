import SwiftUI

struct LoginView: View {
    // 视图持有并管理 ViewModel 的生命周期
    @StateObject private var viewModel: LoginViewModel
    @EnvironmentObject var authService: AuthService
    
    // 用于UI输入的本地状态
    @State private var email = ""
    @State private var password = ""
    
    init(viewModel: LoginViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        // ZStack 用于将加载指示器覆盖在表单之上
        ZStack {
            NavigationView {
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
                }
                .navigationTitle("登录")
            }
            // 当正在加载时，禁用整个NavigationView的交互
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
        .alert(item: $viewModel.alartItem) { alertItem in
            Alert(
                title: Text(alertItem.title),
                message: Text(alertItem.message),
                dismissButton: .default(Text("Ok"))
            )
        }
        .onChange(of: viewModel.isAuthenticated) {isAuthenticated in
            print("➡️ [LoginView.onChange] Detected viewModel.isAuthenticated is now \(isAuthenticated)")
            if isAuthenticated {
                            // 更新全局的 authService
                            self.authService.isAuthenticated = true
                            print("✅ [LoginView.onChange] Successfully updated global authService.isAuthenticated!")
                        }
        }
    }
    
    /// 按钮点击时调用的方法
    private func loginButtonTapped() {
        // 使用 Task 创建一个异步上下文来调用 async 函数
        Task {
            await viewModel.login(email: email, password: password)
        }
    }
}


// MARK: - Xcode 预览 (Preview)
// ===================================
// 这个预览完美地展示了我们架构的优势：
// 我们可以创建一个“假”的网络服务来模拟各种情况，
// 从而在不联网的情况下独立开发和测试UI。
// ===================================

#Preview {
    
    // 1. 创建一个用于预览的 Mock Network Service
    struct MockLoginNetworkService: NetworkServicing {
        func request<T>(endpoint: String, method: HTTPMethod, body: RequestBody?, responseType: T.Type) async throws -> T {
            
            // 模拟我们更新后的两步登录流程
            switch endpoint {
            case "/auth/login":
                // 如果是登录请求，返回一个假的Token
                print("Mock: 正在返回假的Token...")
                let fakeTokenResponse = TokenResponse(
                    accessToken: "fake_preview_token_123",
                    refreshToken: "fake_preview_token_123",
                    tokenType: "Bearer")
                return fakeTokenResponse as! T
                
            case "/users/me":
                // 如果是获取用户信息的请求，返回一个假的用户
                print("Mock: 正在返回假的用户信息...")
                let fakeUser = User(id: UUID(), name: "测试用户", email: "preview@example.com")
                return fakeUser as! T
                
            default:
                // 如果遇到未知的端点，抛出一个错误
                throw NetworkError.invalidURL
            }
        }
    }
    
    // 2. 实例化 Mock 服务和 ViewModel
    let mockNetwork = MockLoginNetworkService()
    let viewModel = LoginViewModel(network: mockNetwork)
    
    // 3. 创建并返回 LoginView
    return LoginView(viewModel: viewModel)
}
