import Foundation
import Combine

class CourseViewModel: ObservableObject, NetworkViewModeling {
    
    @Published var courses: [Course] = []
    
    private let network: NetworkServicing
    
    @Published var isLoading: Bool = false
    @Published var isEnrolling: Bool = false
    @Published var alertItem: AlertItem?
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var allCoursesResponse: AllCoursesResponse? = nil
    
    init(network: NetworkServicing) {
        self.network = network
    }
    
    private func handleError(_ error: Error, title: String) {
        let errorMessage: String
        if let networkError = error as? NetworkError {
            errorMessage = networkError.message
        } else {
            errorMessage = "An unknown error happen: \(error.localizedDescription)"
        }
        alertItem = AlertItem(title: "Enrollment Failed",
                              message: errorMessage)
    }
    

    // MARK: - Fetch all courses from backend
    func fetchAllCourses() async {
        alertItem = nil
        allCoursesResponse = nil
        isLoading = true
        defer { isLoading = false }
        do {
            let endpoint = GetAllCoursesEndpoint()
            let response: AllCoursesResponse = try await network.request(
                endpoint: endpoint,
                responseType: AllCoursesResponse.self
            )
            // Keep the raw response if you want it elsewhere
            self.allCoursesResponse = response
            // Convert and publish the courses array
            // TODO: How to do this problem?
            let covertedCourses =
                response.courses.map{ ConvertResponseToCourse(response: $0) }
            
            await MainActor.run {
                self.courses = covertedCourses
            }
            
        } catch {
            handleError(error, title: "Fetch Course Failed")
        }
    }
    
    // MARK: - convert the response to model
    /// Convert the single course response model -> course model
    func ConvertResponseToCourse(response: CourseResponse) -> Course {
        Course(
            courseId: response.courseId,
            courseName: response.courseName,
            numOfKnowledgeNodes: response.numOfKnowledgeNode,
            isEnrolled: response.isEnrolled,
            isPrimary: false, // TODO: this need to be changed later
            systemImageName: "book" // TODO: this need to be change later
        )
    }
    
    // - MARK: enroll a course
    func enrollInCourse(courseId: String) async {
        isEnrolling = true
        defer { isEnrolling = false }
        alertItem = nil
        enrollmentResponse = nil
        
        do {
            let endpoint = EnrollCourseEndpoint(courseId: courseId)
            let response: EnrollmentResponse = try await network.request(
                endpoint: endpoint,
                responseType: EnrollmentResponse.self
            )
            self.enrollmentResponse = response
            
            // Optionally reflect enrollment state locally
            if let index = courses.firstIndex(where: { $0.courseId == courseId }) {
                var updated = courses[index]
                updated.isEnrolled = true
                courses[index] = updated
            }
        } catch {
            handleError(error, title: "Enrollment Failed")
        }
    }
}
