import SwiftUI

struct HomeView: View {

    @StateObject private var viewModel: DashboardViewModel
    
    @State private var navigateToQuiz = false

    init(viewModel: DashboardViewModel) {
        self._viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                Text("😅😒🤯")
                    .font(.largeTitle)
              
                Button("Start Test Session (G11 Physics)") {
//                    Task {
//                    await viewModel.startSession(courseId: "g11_phys", questionCount: 2)
//                    }
                }
                .padding()
                .background(Color.purple)
                .foregroundColor(.white)
                .cornerRadius(10)
              
                VStack {
                    if viewModel.isEnrolling || viewModel.isStartingSession {
                        ProgressView(viewModel.isEnrolling ? "Enrolling..." : "Starting Session...")
                    }
                    
                    if let response = viewModel.enrollmentResponse {
                        Text("✅ Success! Enrolled with ID: \(response.id.uuidString)")
                            .foregroundColor(.green)
                            .padding()
                    }
                }
                .frame(height: 100)
            }
            .padding()
            .navigationTitle("Welcome")
//            .navigationDestination(item: $viewModel.quizProblemsForNavigation) { problems in
//                QuizView(problems: problems)
//            }
            .alert(item: $viewModel.alertItem) { alertItem in
                Alert(title: Text(alertItem.title), message: Text(alertItem.message), dismissButton: .default(Text("OK")))
            }
        }
    }
}
