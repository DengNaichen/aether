import SwiftUI

struct DashboardView: View {

    @ObservedObject private var viewModel: DashboardViewModel
//    var coordinator: MainCoordinator

    init(viewModel: DashboardViewModel) {
        self._viewModel = ObservedObject(wrappedValue: viewModel)
//        self.coordinator = coordinator
    }

    var body: some View {
        VStack(spacing: 30) {
            Text("😅😒🤯")
                .font(.largeTitle)
            
            Button("Enroll in Default Course(G11 Physics)") {
                Task{
                    await viewModel.enrollInCourse(courseId: "g11_phys")
                }
            }
            .padding()
            .background(Color.green)
            .foregroundColor(.white)
            .cornerRadius(10)
            
            
            Button("Start Test Session (G11 Physics)") {
                Task{
                    do {
                        let response = try await viewModel.startSession(courseId: "g11_phys", questionCount: 2)
                        print("--- 收到 \(response.questions.count) 个问题 ---")
                        for (index, question) in response.questions.enumerated() {
                            print("\(index + 1): \(question)")
                        }
                        print("------------------------")
                        // If navigation is needed, use coordinator here.
                        // coordinator.startQuizSession(with: response)
                    } catch {
                        print("❌ Error starting session: \(error.localizedDescription)")
                    }
                }
            }
            .padding()
            .background(Color.purple)
            .foregroundColor(.white)
            .cornerRadius(10)
        
            
            VStack {
                if viewModel.isEnrolling {
                    ProgressView("Enrolling ...")
                } else if viewModel.isStartingSession {
                    ProgressView("Starting Session ...")
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
