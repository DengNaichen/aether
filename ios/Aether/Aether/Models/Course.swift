import Foundation
import SwiftData
//struct Subject

/// Represents a course data model
///
/// The `Course` structure contains basic information about a course, including
/// the course identifier, name, number of knowledge nodes.
struct Course: Equatable, Identifiable {
    var id = UUID()
    var courseId: String
    var courseName: String
    var numOfKnowledgeNodes: Int
    var isEnrolled: Bool
    /// if the course is primary
    var isPrimary: Bool
}

@Model
final class CourseModel {
    @Attribute(.unique)
    var courseId: String
    var courseName: String
    var courseDescription: String
    var isEnrolled: Bool
    var numOfKnowledgeNodes: Int
    var isPrimary: Bool
    
    init(courseId: String, courseName: String, courseDescription: String,
         isEnrolled: Bool, numOfKnowledgeNodes: Int, isPrimary: Bool) {
        self.courseId = courseId
        self.courseName = courseName
        self.courseDescription = courseDescription
        self.isEnrolled = isEnrolled
        self.numOfKnowledgeNodes = numOfKnowledgeNodes
        self.isPrimary = isPrimary
    }
}

/// A request model for course-related abi calls
///
/// `CourseRequest` is used to encode course identification data when making
/// nerwork request to the backed API, for a single course
struct FetchCourseRequest: Encodable {
    var courseId: String
    
    enum CodingKeys: String, CodingKey {
        case courseId = "course_id"
    }
}

struct FetchCourseResponse: Codable, Equatable {
    // TODO: Define fields when backend schema is available
    var courseId: String
    var courseName: String
    var courseDescription: String
    var isEnrolled: Bool
    var numOfKnowledgeNode: Int

    enum CodingKeys: String, CodingKey {
        case courseId = "course_id"
        case courseName = "course_name"
        case courseDescription = "course_description"
        case isEnrolled = "is_enrolled"
        case numOfKnowledgeNode = "num_of_knowledge"  // Backend uses "num_of_knowledge" not "num_of_knowledge_nodes"
    }
}

struct FetchAllCoursesRequest: Codable, Equatable {
    // TODO: Seems I don't need it, but I will just keep it for a while
}

// Response is directly an array, not wrapped in an object
typealias FetchAllCoursesResponse = [FetchCourseResponse]

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
