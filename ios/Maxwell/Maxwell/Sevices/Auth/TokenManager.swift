import Foundation
import KeychainAccess

class TokenManager {
    static let shared = TokenManager()
    
    private let keychain = Keychain(service: Bundle.main.bundleIdentifier ?? "com.example.yourapp")
    
    private let accessTokenKey = "auth_access_token"
    private let refreshTokenKey = "auth_refresh_token"
    
    private init() {}
    
    func saveTokens(accessToken: String, refreshToken: String) {
        keychain[accessTokenKey] = accessToken
        keychain[refreshTokenKey] = refreshToken
        print("Tokens saved to KeyChain")
    }
    
    func getAccessToken() -> String? {
        return keychain[accessTokenKey]
    }
    
    func getRefreshToken() -> String? {
        return keychain[refreshTokenKey]
    }
    
    func clearToken() {
        keychain[accessTokenKey] = nil
        keychain[refreshTokenKey] = nil
        print("Tokens cleared form Keychain.")
    }
}
