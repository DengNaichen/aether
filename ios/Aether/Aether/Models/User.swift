import Foundation

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct TokenResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
    }
}

struct RefreshTokenRequest: Encodable {
    let refreshToken: String

    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
}

// MARK: - 1. 数据模型 (与 FastAPI 的 Pydantic 模型对应)
// structure of sending server
struct RegistrationRequest: Encodable {
    let name: String
    let email: String
    let password: String
}

// struct of recieving from serverr
struct RegistrationResponse: Decodable {
    let id: UUID
    let name: String
    let email: String
    let createdAt: Date
    
    private enum CodingKeys: String, CodingKey {
        case id, name, email
        case createdAt = "created_at"
    }
}


struct ErrorResponse: Codable {
    let detail: String
}


struct User: Codable {
    let id: UUID
    let name: String
    let email: String
}

// MARK: - Social Login Request Models
struct AppleSignInRequest: Encodable {
    let userID: String
    let identityToken: String
    let email: String
    let firstName: String
    let lastName: String
    
    enum CodingKeys: String, CodingKey {
        case userID = "user_id"
        case identityToken = "identity_token"
        case email
        case firstName = "first_name"
        case lastName = "last_name"
    }
}

struct GoogleSignInRequest: Encodable {
    let userID: String
    let idToken: String
    let email: String
    let firstName: String
    let lastName: String
    
    enum CodingKeys: String, CodingKey {
        case userID = "user_id"
        case idToken = "id_token"
        case email
        case firstName = "first_name"
        case lastName = "last_name"
    }
}
