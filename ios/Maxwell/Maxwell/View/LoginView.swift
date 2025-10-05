// LoginView.swift

import SwiftUI

struct LoginView: View {
    // 1. 使用 @StateObject 创建并持有 ViewModel 的实例
    // SwiftUI 会负责管理它的生命周期
    @StateObject private var viewModel = LoginViewModel()

    var body: some View {
        NavigationStack {
            // 2. 根据 ViewModel 的 isAuthenticated 状态来决定显示哪个视图
            if viewModel.isAuthenticated {
                // 登录成功后，显示欢迎信息
                // 在真实应用中，这里会导航到应用的主内容视图
                VStack(spacing: 20) {
                    Text("登录成功!")
                        .font(.largeTitle).bold()
                    Text("欢迎回来, \(viewModel.email)")
                        .font(.headline)
                        .foregroundStyle(.secondary)
                }
            } else {
                // 未登录时，显示登录表单
                loginForm
            }
        }
    }
    
    // 将登录表单提取为一个计算属性，使 body 更整洁
    private var loginForm: some View {
        // 3. 使用 ZStack 来方便地在所有内容之上覆盖一个加载指示器
        ZStack {
            VStack(spacing: 25) {
                
                // --- 标题 ---
                VStack(spacing: 10) {
                    Image(systemName: "lock.shield.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.blue)
                    Text("欢迎登录")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                }
                .padding(.bottom, 20)

                // --- 输入框 ---
                VStack(spacing: 15) {
                    // 4. 将 TextField 的 text 与 ViewModel 的属性进行双向绑定
                    TextField("邮箱地址", text: $viewModel.email)
                        .padding()
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)

                    SecureField("密码", text: $viewModel.password)
                        .padding()
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                        .textContentType(.password)
                }

                // --- 登录按钮 ---
                Button(action: viewModel.login) { // 5. 按钮的 action 直接调用 ViewModel 的方法
                    Text("登录")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(height: 55)
                        .frame(maxWidth: .infinity)
                        .background(Color.blue)
                        .cornerRadius(12)
                }
                // 6. 根据加载状态禁用按钮，防止用户重复点击
                .disabled(viewModel.isLoading)

                // --- 错误信息 ---
                // 7. 如果 errorMessage 不为空，就显示错误信息
                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                        .padding(.top, 10)
                }
                
                Spacer() // 将所有内容推向顶部
            }
            .padding(.horizontal, 30)
            .padding(.top, 40)
            
            // --- 加载遮罩 ---
            // 8. 如果正在加载，显示一个半透明的遮罩和加载动画
            if viewModel.isLoading {
                Color.black.opacity(0.4)
                    .edgesIgnoringSafeArea(.all)
                
                ProgressView("登录中...")
                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    .scaleEffect(1.5)
                    .foregroundColor(.white)
            }
        }
    }
}

#Preview {
    LoginView()
}
