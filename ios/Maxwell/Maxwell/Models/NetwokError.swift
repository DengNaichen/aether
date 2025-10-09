import Foundation

struct ErrorDetail: Decodable, Error {
    let detail: String
}

enum NetworkError: Error {
    case invalidURL
    case decodingFailed
    case tokenNotFound
    case clientError(String)
    case serverError(String)
    case unknownError
    
    
    var message: String {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .decodingFailed: return "Failed to parse server response"
        case .tokenNotFound: return "Token Not found"
        case .clientError(let msg): return msg
        case .serverError(let msg): return msg
        case .unknownError: return "Unknown network error"
        }
    }
}

