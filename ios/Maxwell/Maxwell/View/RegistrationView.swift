import SwiftUI

// MARK: - 2. UI 视图和逻辑

struct RegistrationView: View {
    @StateObject var viewModel: RegistrationViewModel
    
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    
    @Environment(\.dismiss) private var dismiss
    
    init(viewModel: RegistrationViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Personal Info")) {
                    TextField("Name", text: $name).autocapitalization(.words)
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                }
                
                Section(header: Text("Password")) {
                    SecureField("Enter Password", text: $password)
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
                    .disabled($name.isEmpty || $email.isEmpty || $password.isEmpty)
                }
            }
            .navigationTitle("RegistrationView")
            .onChange(of: viewModel.registrationSuccessful) { success in
                if success {
                    print("successfully, prepare to close the page")
                    dismiss
                }
            }
        }
    }
}


// 这是为了在 Xcode 预览中看到视图
#Preview() {
    RegistrationView()
}
