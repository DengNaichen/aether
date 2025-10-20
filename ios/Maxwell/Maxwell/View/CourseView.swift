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
                
                Text("\(course.numOfKnowledgeNodes)")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            Spacer()
        }
        .padding(.vertical, 8)
    }
}


struct CoursesListView: View {
    @StateObject private var viewModel = CourseViewModel()
    
    var body: some View {
        NavigationView{
            List(viewModel.courses) { course in
                NavigationLink(
                    destination: Text("details: \(course.courseName)")
                ) {
                    CourseRowView(course: course)
                }
            }
            .listStyle(.plain)
            .navigationTitle(Text("Courses"))
            .onAppear {
                viewModel.fetchCourses()
            }
        }
    }
}


#Preview {
    CoursesListView()
}
