import SwiftUI

// MARK: - 2. UI 视图和逻辑

struct RegistrationView: View {
    @StateObject var rMV = RegistrationViewModel()

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Personal Info")) {
                    TextField("Name", text: $rMV.name)
                        .autocapitalization(.words) // 姓名首字母大写
                    TextField("Email", text: $rMV.email)
                        .keyboardType(.emailAddress) // 弹出邮箱专用键盘
                        .autocapitalization(.none)
                }
                
                Section(header: Text("Password")) {
                    SecureField("Enter Password", text: $rMV.password) // 密码安全输入框
                }
                
                Section {
                    Button(action: rMV.registerUser) {
                        // 让按钮充满整个可用宽度
                        HStack {
                            Spacer()
                            Text("Register")
                            Spacer()
                        }
                    }
                    // 按钮在所有字段都填写后才可用
                    .disabled(rMV.name.isEmpty || rMV.email.isEmpty || rMV.password.isEmpty)
                }
            }
            .navigationTitle("注册新学生")
            // 弹窗，用于显示注册成功或失败的消息
            .alert(isPresented: $rMV.showAlert) {
                Alert(title: Text("注册结果"), message: Text(rMV.alertMessage), dismissButton: .default(Text("好的")))
            }
        }
    }
}


// 这是为了在 Xcode 预览中看到视图
#Preview() {
    WelcomeView()
}
