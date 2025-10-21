import Foundation

struct SessionStartRequest: Codable, Equatable {
    let courseId: String

    enum CodingKeys: String, CodingKey {
        case courseId = "course_id"
    }
}

struct SessionStartResponse: Codable, Equatable {
    let sessionId: UUID
    let studentId: UUID
    let courseId: String
    let sessionDate: Date
    let questions: [AnyQuestion]
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case studentId = "student_id"
        case courseId = "course_id"
        case sessionDate = "session_date"
        case questions = "questions"
    }
}
