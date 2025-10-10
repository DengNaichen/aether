import SwiftUI

struct RegisterView: View {
    @ObservedObject var viewModel: RegisterViewModel
    @EnvironmentObject var coordinator: OnboardingCoordinator
    
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
                    Section(header: Text("个人信息")) {
                        TextField("姓名", text: $name)
                            .autocapitalization(.words)
                        TextField("邮箱", text: $email)
                            .keyboardType(.emailAddress)
                            .autocapitalization(.none)
                            .textContentType(.emailAddress)
                    }
                    
                    Section(header: Text("密码")) {
                        SecureField("输入密码", text: $password)
                            .textContentType(.newPassword)
                    }
                    
                    Section {
                        Button(action: registerButtonTapped) {
                            HStack {
                                Spacer()
                                Text("注册")
                                Spacer()
                            }
                        }
                        .disabled(!isFormedValid || viewModel.isLoading)
                    }
                    
                    Section {
                        Button("已有账户? 返回登录") {
                            coordinator.showLoginView()
                        }
                        .tint(.secondary)
                    }
                }
                .navigationTitle("注册新学生")
            }
            .disabled(viewModel.isLoading)
            
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
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(title: Text(alertItem.title),
                  message: Text(alertItem.message),
                  dismissButton: .default(Text("OK"))
            )
        }
    }
    private func registerButtonTapped() {
        Task {
            UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
            await viewModel.register(username: name, email: email, password: password)
        }
    }
}


// MARK: - Xcode 预览
//struct MockNetworkService: NetworkServicing {
//    func request<T: Decodable>(endpoint: String,
//                       method: HTTPMethod,
//                       body: RequestBody?,
//                       responseType: T.Type)
//    async throws -> T {
//        
//        try await Task.sleep(nanoseconds: 2_000_000_000)
//        if T.self == RegistrationResponse.self{
//            let mockResponse = RegistrationResponse(
//                id: UUID(),
//                name: "Mock user",
//                email: "mock@example.com",
//                createdAt: Date()
//            )
//            return mockResponse as! T
//        }
//        let errorDescription = "Mock for the type \(T.self) in not implemented in MockNetworkService."
//        throw NSError(domain: "MockNetworkServiceError", code: 404, userInfo: [NSLocalizedDescriptionKey: errorDescription])
//    }
//}
//
//#Preview {
//    // 在预览中，我们注入一个 Mock 的网络服务
//    // 这样预览就不依赖于真实的网络，速度快且稳定
//    let mockNetwork = MockNetworkService()
//    let viewModel = RegistrationViewModel(network: mockNetwork)
//    return RegistrationView(viewModel: viewModel)
//}
