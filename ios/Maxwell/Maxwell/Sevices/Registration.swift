import Foundation

// MARK: - 1. 数据模型 (与 FastAPI 的 Pydantic 模型对应)
// structure of sending server
struct RegistrationRequest: Encodable {
    let name: String
    let email: String
    let password: String
}

// struct of recieving from serverr
struct RegistrationResponse: Decodable {
    let id: Int
    let name: String
    let email: String
    let createdAt: Date
    
    private enum CodingKeys: String, CodingKey {
        case id, name, email
        case createdAt = "created_at"
    }
}
