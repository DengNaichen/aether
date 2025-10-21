import Foundation
import SwiftData
import Combine

@MainActor
class CourseViewModel: ObservableObject, NetworkViewModeling {
    
    @Published var courses: [Course] = []
    
    private let network: NetworkServicing
    private let modelContext: ModelContext
    
    @Published var isLoading: Bool = false
    @Published var isEnrolling: Bool = false
    @Published var alertItem: AlertItem?
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var allCoursesResponse: FetchAllCoursesResponse? = nil
    
    init(network: NetworkServicing, modelContext: ModelContext) {
        self.network = network
        self.modelContext = modelContext
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
            let response: FetchAllCoursesResponse = try await network.request(
                endpoint: endpoint,
                responseType: FetchAllCoursesResponse.self
            )
            // Keep the raw response if you want it elsewhere
            self.allCoursesResponse = response
            
            let courseModels = response.courses.map {convertResponseToCourseModel (response: $0)}

            try persist(courseModels: courseModels)
            
            loadCoursesFromDB()
            
            
        } catch {
            handleError(error, title: "Fetch Course Failed")
        }
    }
    
    // MARK: - Model Conversion Helpers
    func convertResponseToCourseModel(response: FetchCourseResponse)
    -> CourseModel {
        return CourseModel(
            courseId: response.courseId,
            courseName: response.courseName,
            courseDescription: response.courseDescription,
            isEnrolled: response.isEnrolled,
            numOfKnowledgeNodes: response.numOfKnowledgeNode,
            isPrimary: false // TODO: login, this need to be changed later
        )
    }
    
    /// Convert the single course response model -> course model
    func ConvertCourseModelToCourse(model: CourseModel) -> Course {
        Course(
            courseId: model.courseId,
            courseName: model.courseName,
            numOfKnowledgeNodes: model.numOfKnowledgeNodes,
            isEnrolled: model.isEnrolled,
            isPrimary: model.isPrimary
        )
    }
    
    private func persist(courseModels: [CourseModel]) throws {
        try modelContext.delete(model: CourseModel.self)
        for model in courseModels {
            modelContext.insert(model)
        }
        try modelContext.save()
    }
    
    @MainActor
    private func loadCoursesFromDB() {
        do {
            let descriptor = FetchDescriptor<CourseModel>(sortBy: [SortDescriptor(\.courseName)])
            let models = try modelContext.fetch(descriptor)
            self.courses = models.map{ ConvertCourseModelToCourse(model: $0)}
        } catch {
            handleError(error, title: "Failed to load courses from database")
        }
        
    }
    
    // MARK: - enroll a course
    func enrollInCourse(courseId: String) async {
        // TODO: a local login to check if the user already enrolled this course
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
