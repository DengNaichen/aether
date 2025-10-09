import SwiftUI

struct WelcomeView: View {
    @EnvironmentObject private var networkService: NetworkService
    
    @StateObject private var viewModel: EnrollmentViewModel
    
    init(viewModel: EnrollmentViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                Text("😅😒🤯")
                    .font(.largeTitle)
                NavigationLink(destination:QuizView()) {
                    Text("Start a quiz")
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
                
                Button("Enroll in Default Course(G11 Physics)") {
                    Task{
                        await viewModel.enrollInCourse(courseId: "g11_phys")
                    }
                }
                .padding()
                .background(Color.green)
                .foregroundColor(.white)
                .cornerRadius(10)
                .disabled(viewModel.isLoading)
                
                VStack {
                    if viewModel.isLoading {
                        ProgressView("Enrolling ...")
                    }
                    if let response = viewModel.enrollmentResponse {
                        Text("✅ Success! Enrolled with ID: \(response.id.uuidString)")
                            .foregroundColor(.green)
                            .padding()
                    }
                    if let errorMessage = viewModel.alartItem?.message {
                        Text("❌ Error: \(errorMessage)")
                            .foregroundColor(.red)
                            .padding()
                    }
                }
                .frame(height: 100)
            }
            .padding()
            .navigationTitle("Welcome")
        }
    }
}


//#Preview {
//    WelcomeView()
//}
