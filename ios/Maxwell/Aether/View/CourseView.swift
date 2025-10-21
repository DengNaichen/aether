import SwiftUI

struct CourseRowView: View {
    let course: Course
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: course.systemImageName)
                .font(.largeTitle)
                .foregroundStyle(.blue)
                .frame(width: 50, height: 50)
                .background(Color.blue.opacity(0.1))
                .clipShape(Circle())
            VStack(alignment: .leading, spacing: 4) {
                
                Text(course.courseName)
                    .font(.headline)
                    .fontWeight(.bold)
                
                Text("\(course.numOfKnowledgeNodes) nodes")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
            }
            Spacer()
        }
        .padding(.vertical, 8)
    }
}

struct CourseDetailView: View {
    let course: Course
    @ObservedObject var viewModel: CourseViewModel
    
    
    var body: some View {
        Button("Enroll in \(course.courseName)") {
            Task {
                await viewModel.enrollInCourse(courseId: course.courseId)
            }
        }
    }
}


struct CoursesListView: View {
    
    @StateObject private var viewModel: CourseViewModel
    
    init(viewModel: CourseViewModel) {
        self._viewModel = StateObject(wrappedValue: viewModel)
    }
    
    var body: some View {
        NavigationView{
            List(viewModel.courses) { course in
                NavigationLink(
                    destination: CourseDetailView(
                        course: course,
                        viewModel: viewModel
                    )
                ) {
                    CourseRowView(course: course)
                }
            }
            .listStyle(.plain)
            .navigationTitle(Text("Courses"))
            .onAppear {
                Task {
                    // TODO: if this fail, we need a new error handler
                    await viewModel.fetchAllCourses()
                }
            }
        }
    }
}


//#Preview {
//    CoursesListView()
//}
