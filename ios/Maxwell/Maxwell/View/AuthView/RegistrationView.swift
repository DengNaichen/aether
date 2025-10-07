import SwiftUI

struct RegistrationView: View {
    @StateObject private var viewModel: RegistrationViewModel
    
    // 2. 使用 @State 管理只与此视图相关的输入状态
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    
    // 用于在注册成功后关闭视图
    @Environment(\.dismiss) private var dismiss
    
    private var isFormedValid: Bool {
        !name.isEmpty && email.contains("@") && password.count >= 6
    }

    // 自定义 init 以接受注入的 ViewModel
    // 这使得视图的创建和依赖注入分离
    init(viewModel: RegistrationViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        // 使用 ZStack 将加载动画覆盖在表单之上
        ZStack {
            NavigationView {
                Form {
                    Section(header: Text("个人信息")) {
                        TextField("姓名", text: $name)
                            .autocapitalization(.words)
                        TextField("邮箱", text: $email)
                            .keyboardType(.emailAddress)
                            .autocapitalization(.none)
                            .textContentType(.emailAddress) // 增强自动填充功能
                    }
                    
                    Section(header: Text("密码")) {
                        SecureField("输入密码", text: $password)
                            .textContentType(.newPassword) // 增强密码管理功能
                    }
                    
                    Section {
                        Button(action: registerButtonTapped) {
                            HStack {
                                Spacer()
                                Text("注册")
                                Spacer()
                            }
                        }
                        // 根据 @State 属性判断按钮是否可用
                        .disabled(!isFormedValid || viewModel.isLoading)
                    }
                }
                .navigationTitle("注册新学生")
            }
            // 禁用表单交互当正在加载时
            .disabled(viewModel.isLoading)
            
            // 4. 根据 isLoading 状态显示加载动画
            if viewModel.isLoading {
                ProgressView("注册中...")
                    .progressViewStyle(CircularProgressViewStyle())
                    .padding()
                    .background(Color.secondary.colorInvert())
                    .cornerRadius(10)
                    .shadow(radius: 10)
                    .transition(.opacity.animation(.easeInOut))
            }
        }
        // 5. 根据 errorMessage 显示错误弹窗
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(title: Text(alertItem.title),
                  message: Text(alertItem.message),
                  dismissButton: .default(Text("OK"))
            )
        }
        .onChange(of: viewModel.registrationSuccessful) { oldValue, newValue in
            if newValue {
                print("注册成功, 要关闭页面")
                dismiss()
            }
        }
    }
    
    // 3. 按钮的 Action，使用 Task 调用异步函数
    private func registerButtonTapped() {
        Task {
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
            await viewModel.register(username: name, email: email, password: password)
        }
    }
}


// MARK: - Xcode 预览
struct MockNetworkService: NetworkServicing {
    func request<T: Decodable>(endpoint: String,
                       method: HTTPMethod,
                       body: RequestBody?,
                       responseType: T.Type)
    async throws -> T {
        
        try await Task.sleep(nanoseconds: 2_000_000_000)
        if T.self == RegistrationResponse.self{
            let mockResponse = RegistrationResponse(
                id: UUID(),
                name: "Mock user",
                email: "mock@example.com",
                createdAt: Date()
            )
            return mockResponse as! T
        }
        let errorDescription = "Mock for the type \(T.self) in not implemented in MockNetworkService."
        throw NSError(domain: "MockNetworkServiceError", code: 404, userInfo: [NSLocalizedDescriptionKey: errorDescription])
    }
}

#Preview {
    // 在预览中，我们注入一个 Mock 的网络服务
    // 这样预览就不依赖于真实的网络，速度快且稳定
    let mockNetwork = MockNetworkService()
    let viewModel = RegistrationViewModel(network: mockNetwork)
    return RegistrationView(viewModel: viewModel)
}
