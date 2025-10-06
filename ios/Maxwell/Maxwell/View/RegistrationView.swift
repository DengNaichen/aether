import SwiftUI

struct RegistrationView: View {
    // 1. 将 ViewModel 作为环境对象或由父视图传入
    // 我们在这里使用 @StateObject 进行初始化，并在 #Preview 中展示如何注入依赖
    @StateObject private var viewModel: RegistrationViewModel
    
    // 2. 使用 @State 管理只与此视图相关的输入状态
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    
    // 用于在注册成功后关闭视图
    @Environment(\.dismiss) private var dismiss

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
                        .disabled(name.isEmpty || email.isEmpty || password.isEmpty || viewModel.isLoading)
                    }
                }
                .navigationTitle("注册新学生")
                // 当 viewModel 的 registrationSuccessful 变为 true 时触发
                .onChange(of: viewModel.registrationSuccessful) { success in
                    if success {
                        // 注册成功后可以执行操作，比如延迟一秒后关闭当前视图
                        // 这里可以显示一个更友好的成功提示，然后再关闭
                        print("注册成功，准备关闭页面...")
                        dismiss()
                    }
                }
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
            }
        }
        // 5. 根据 errorMessage 显示错误弹窗
        .alert("注册失败", isPresented: .constant(viewModel.errorMessage != nil), actions: {
            Button("好的") {
                viewModel.errorMessage = nil // 点击按钮后清除错误信息
            }
        }, message: {
            Text(viewModel.errorMessage ?? "")
        })
    }
    
    // 3. 按钮的 Action，使用 Task 调用异步函数
    private func registerButtonTapped() {
        Task {
            await viewModel.register(username: name, email: email, password: password)
        }
    }
}


// MARK: - Xcode 预览
// ===================================

// 为了让预览正常工作，并且展示依赖注入的强大之处，
// 我们创建一个 Mock Network Service
struct MockNetworkService: NetworkServicing {
    func request<T, U>(endpoint: String,
                       method: HTTPMethod,
                       body: U?,
                       responseType: T.Type)
    async throws -> T where T : Decodable, T : Sendable, U : Encodable {
        // 模拟一个成功的返回，这里我们用 TokenResponse
        // 确保你的项目里有 TokenResponse 这个结构体
        return TokenResponse(accessToken: "fake_mock_token",
                             tokenType: "Bearer") as! T
    }
}

#Preview {
    // 在预览中，我们注入一个 Mock 的网络服务
    // 这样预览就不依赖于真实的网络，速度快且稳定
    let mockNetwork = MockNetworkService()
    let viewModel = RegistrationViewModel(network: mockNetwork)
    return RegistrationView(viewModel: viewModel)
}
