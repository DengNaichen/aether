import SwiftUI

// MARK: - Login Info Section
struct LoginInfoSection: View {
    @Binding var email: String
    
    var body: some View {
        Section(header: Text("Personal Information")) {

            TextField("Email", text: $email)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .textContentType(.emailAddress)
        }
    }
}

// MARK: - Personal Info Section
struct PersonalInfoSection: View {
    @Binding var name: String
    @Binding var email: String
    
    var body: some View {
        Section(header: Text("Personal Information")) {
            TextField("Name", text: $name)
                .autocapitalization(.words)
            
            TextField("Email", text: $email)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .textContentType(.emailAddress)
        }
    }
}

// MARK: - Password Section
struct PasswordSection: View {
    @Binding var password: String
    
    var body: some View {
        Section(header: Text("Password")) {
            SecureField("Password", text: $password)
                .textContentType(.newPassword)
        }
    }
}

// MARK: - Register Button Section
struct RegisterButtonSection: View {
    let text: String
    let isEnable: Bool
    let action: () -> Void
    
    var body: some View {
        Section {
            Button(action: action) {
                HStack {
                    Spacer()
                    Text(text)
                    Spacer()
                }
            }
            .disabled(!isEnable)
        }
    }
}

// MARK: - Login Navigation Section
struct LoginNavigationSection: View {
    var text: String
    let action: () -> Void
    
    var body: some View {
        Section {
            Button(text) {
                action()
            }
            .tint(.secondary)
        }
    }
}

// MARK: - Loading Overlay
struct LoadingOverlay: View {
    let message: String
    
    var body: some View {
        ProgressView("message")
            .progressViewStyle(CircularProgressViewStyle())
            .padding()
            .background(Color.secondary.colorInvert())
            .cornerRadius(10)
            .shadow(radius: 10)
            .transition(.opacity.animation(.easeInOut))
    }
}

