import Foundation

struct EnrollmentRequest: Encodable {
    let courseId: String
    
    enum CodingKeys: String, CodingKey {
        case courseId = "course_id"
    }
}

struct EnrollmentResponse: Codable, Equatable {
    let id: UUID
    let studentId: UUID
    let courseId: String
    let enrollmentDate: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case studentId = "student_id"
        case courseId = "course_id"
        case enrollmentDate = "enrollment_date"
    }
}
