import SwiftUI
import AuthenticationServices
import GoogleSignInSwift

struct AuthHeaderView: View {
    let title: String
    let subtitle: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(title)
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text(subtitle)
                .font(.headline)
                .foregroundColor(.secondary)
        }
        .padding(.bottom, 32)
    }
}


struct AuthTextField: View {
    let placeholder: String
    @Binding var text: String
    var isSecure: Bool = false
    
    var body: some View {
        Group {
            if isSecure {
                SecureField(placeholder, text: $text)
            } else {
                TextField(placeholder, text: $text)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
        .autocapitalization(.none)
        .keyboardType(placeholder.lowercased() == "email" ? .emailAddress : .default)
    }
}

struct AuthButton: View {
    let title: String
    let action: () -> Void
    var isEnabled: Bool = true
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .fontWeight(.semibold)
                .frame(maxWidth: .infinity)
                .padding()
                .background(isEnabled ? Color.accentColor : Color.gray)
                .foregroundColor(.white)
                .cornerRadius(10)
        }
        .disabled(!isEnabled)
    }
}

struct SocialLoginButton: View {
    @Environment(\.colorScheme) var colorScheme

    let provider: String
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                if provider == "Apple" {
                    Image(systemName: "applelogo")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 20, height: 20)
                        .foregroundColor(colorScheme == .dark ? .white : .black)
                } else {
                    Image(provider.lowercased()) // Assumes you have "google" asset
                        .resizable()
                        .scaledToFit()
                        .frame(width: 24, height: 24)
                }
                
                Text(title)
                    .fontWeight(.medium)
                    .foregroundColor(titleColor)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(buttonBackground)
            .cornerRadius(10)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(buttonBorder, lineWidth: 1)
            )
        }
    }

    private var titleColor: Color {
        if provider == "Apple" {
            return colorScheme == .dark ? .white : .black
        } else {
            return colorScheme == .dark ? .white : .black.opacity(0.75)
        }
    }

    private var buttonBackground: Color {
        switch (provider, colorScheme) {
        case ("Apple", .dark):
            return .black
        case ("Apple", .light):
            return .white
        case ("Google", .dark):
            return Color(white: 0.25) // Dark gray for Google in dark mode
        case ("Google", .light):
            return .white
        default:
            return Color(.systemGray5)
        }
    }
    
    private var buttonBorder: Color {
        switch (provider, colorScheme) {
        case ("Apple", .light):
            return .black
        case ("Apple", .dark):
            return .white // White border for Apple in dark mode
        case ("Google", .light):
            return Color(.systemGray4) // Subtle border for Google in light mode
        default:
            return .clear
        }
    }
}

struct OrDivider: View {
    var body: some View {
        HStack {
            VStack { Divider() }
            Text("OR")
                .font(.caption)
                .foregroundColor(.secondary)
            VStack { Divider() }
        }
    }
}

struct AuthNavigationLink: View {
    let prompt: String
    let actionText: String
    let action: () -> Void
    
    var body: some View {
        HStack {
            Text(prompt)
            Button(action: action) {
                Text(actionText)
                    .fontWeight(.semibold)
            }
        }
        .font(.footnote)
    }
}

// MARK: - Loading Overlay
struct LoadingOverlay: View {
    let message: String
    
    var body: some View {
        ZStack {
            Color.black.opacity(0.1)
                .edgesIgnoringSafeArea(.all)
            
            VStack {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle())
                Text(message)
                    .padding(.top, 8)
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(10)
            .shadow(radius: 10)
        }
    }
}

// MARK: - Native Apple Sign-In Button Wrapper
struct AppleSignInButtonView: View {
    @Environment(\.colorScheme) private var colorScheme
    
    let title: String
    let action: () -> Void
    var cornerRadius: CGFloat = 10
    
    var body: some View {
        SignInWithAppleButton(.signIn, onRequest: { _ in
            // Keep empty for now; you’ll configure requests later.
        }, onCompletion: { _ in
            // Placeholder: you’ll handle result later.
            action()
        })
        .signInWithAppleButtonStyle(colorScheme == .dark ? .white : .black)
        .frame(maxWidth: .infinity, minHeight: 50)
        .cornerRadius(cornerRadius)
        .accessibilityLabel(Text(title))
    }
}

struct GoogleSignInButtonView: View {
    @Environment(\.colorScheme) private var colorScheme
    var action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                // Google Logo with brand colors
                ZStack {
                    Circle()
                        .fill(Color.white)
                        .frame(width: 20, height: 20)
                    
                    Image(systemName: "g.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.blue)
                }
                
                Text("Sign in with Google")
                    .font(.system(size: 17, weight: .medium))
                    .foregroundColor(textColor)
            }
            .frame(maxWidth: .infinity, minHeight: 50)
            .background(backgroundColor)
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(borderColor, lineWidth: 1)
            )
            .cornerRadius(10)
        }
    }
    
    private var backgroundColor: Color {
        colorScheme == .dark ? Color(white: 0.15) : Color.white
    }
    
    private var textColor: Color {
        colorScheme == .dark ? Color.white : Color(white: 0.2)
    }
    
    private var borderColor: Color {
        colorScheme == .dark ? Color(white: 0.3) : Color(white: 0.85)
    }
}

