import Foundation
import Combine

class CourseViewModel: ObservableObject {
    
    @Published var courses: [Course] = []
    
    func fetchCourses() {
        self.courses = [
            Course(
                courseId: "g11_chem",
                courseName: "G11 Chemistry",
                numOfKnowledgeNodes: 100,
                isEnrolled: true,
                isPrimary: true,
                systemImageName: "flash"
            ),
            Course(
                courseId: "g11_phys",
                courseName: "G11 Physics",
                numOfKnowledgeNodes: 85,
                isEnrolled: true,
                isPrimary: false,
                systemImageName: "atom"
            ),
            Course(
                courseId: "g12_math",
                courseName: "G12 Mathematics",
                numOfKnowledgeNodes: 50,
                isEnrolled: false,
                isPrimary: false,
                systemImageName: "function")
        ]
    }
}
