import Foundation

//struct Subject

/// Represents a course data model
///
/// The `Course` structure contains basic information about a course, including
/// the course identifier, name, number of knowledge nodes.
struct Course: Equatable, Identifiable {
    var id = UUID()
    /// The unique indentifier for the course
    var courseId: String
    /// the name of the course
    var courseName: String
    /// The number of knowledge nodes contained in the course
    var numOfKnowledgeNodes: Int
    /// The enrollment status, will be used for Views
    var isEnrolled: Bool
    /// if the course is primary
    var isPrimary: Bool
    ///
    var systemImageName: String
}

/// A request model for course-related abi calls
///
/// `CourseRequest` is used to encode course identification data when making
/// nerwork request to the backed API, for a single course
struct CourseRequest: Encodable {
    var courseId: String
    
    enum CodingKeys: String, CodingKey {
        case courseId = "course_id"
    }
}

struct CourseResponse: Codable, Equatable {
    // TODO: Define fields when backend schema is available
    var courseId: String
    var courseName: String
    var isEnrolled: Bool
    var numOfKnowledgeNode: Int
    
    enum CodingKeys: String, CodingKey {
        case courseId = "course_id"
        case courseName = "course_name"
        case isEnrolled = "is_enrolled"
        case numOfKnowledgeNode = "num_of_knowledge_nodes"
    }
}

struct AllCoursesRequest: Codable, Equatable {
    // TODO: Seems I don't need it, but I will just keep for a while
}

struct AllCoursesResponse: Codable, Equatable {
    var courses: [CourseResponse]
}

struct EnrollmentRequest: Encodable, Equatable {
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
