import SwiftUI
import CoreHaptics

struct QuizCompletionView: View {
    @ObservedObject var viewModel: QuizViewModel
    @State private var showConfetti = false

    var body: some View {
        ZStack {
            if showConfetti {
                ConfettiView()
                    .edgesIgnoringSafeArea(.all)
            }
            
            VStack(spacing: 20) {
                Text("Quiz Finished! 🥳")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Your Score:")
                    .font(.title2)
                
                // Add safety check for empty questions array
                if !viewModel.questions.isEmpty {
                    Text("\(viewModel.score) / \(viewModel.questions.count)")
                        .font(.system(size: 60, weight: .bold))
                } else {
                    Text("Score unavailable")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
                
                Button(action: {
                    Task {
                        await viewModel.submitQuiz()
                    }
                }) {
                    HStack {
                        if viewModel.isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                                .padding(.trailing, 5)
                        }
                        Text(viewModel.isLoading ? "提交中..." : "提交答案")
                    }
                    .font(.headline)
                    .fontWeight(.bold)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(viewModel.isLoading ? .gray : .blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(viewModel.isLoading)
            }
        }
        .onAppear {
            showConfetti = true
            triggerHapticFeedback()
        }
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(
                title: Text(alertItem.title),
                message: Text(alertItem.message),
                dismissButton: .default(Text("确定"))
            )
        }
    }

    private func triggerHapticFeedback() {
        // Add error handling for haptic feedback
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else {
            // Fallback to simple impact feedback
            let generator = UIImpactFeedbackGenerator(style: .medium)
            generator.impactOccurred()
            return
        }
        
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.success)
    }
}

#if DEBUG
import SwiftData

struct QuizCompletionView_Previews: PreviewProvider {
    static var previews: some View {
        // Create a mock setup for preview
        let mockContainer = try! ModelContainer(
            for: QuizAttempt.self, StoredQuestion.self,
            configurations: .init(isStoredInMemoryOnly: true)
        )
        
        let mockNetwork = MockNetworkService()
        let viewModel = QuizViewModel(
            network: mockNetwork,
            modelContext: mockContainer.mainContext
        )
        
        // Set up mock data for completed quiz
        viewModel.score = 8
        
        // Create mock StoredQuestions first
        let mockQuestion1 = StoredQuestion(
            id: UUID(),
            text: "Mock Question 1",
            type: .multipleChoice,
            detailsJSON: """
            {
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0
            }
            """,
            isSubmitted: true,
            selectedOptionIndex: 0,
            userTextAnswer: nil
        )
        
        let mockQuestion2 = StoredQuestion(
            id: UUID(),
            text: "Mock Question 2",
            type: .multipleChoice,
            detailsJSON: """
            {
                "options": ["A", "B", "C", "D"],
                "correct_answer": 1
            }
            """,
            isSubmitted: true,
            selectedOptionIndex: 1,
            userTextAnswer: nil
        )
        
        // Insert mock questions into the model context
        mockContainer.mainContext.insert(mockQuestion1)
        mockContainer.mainContext.insert(mockQuestion2)
        
        // Create QuestionDisplay objects from StoredQuestions
        viewModel.questions = [
            QuestionDisplay(from: mockQuestion1),
            QuestionDisplay(from: mockQuestion2)
        ]
        
        return Group {
            // Main preview with full quiz completion view
            QuizCompletionView(viewModel: viewModel)
                .modelContainer(mockContainer)
                .previewDisplayName("Quiz Completion")
            
            // Confetti animation test
            ConfettiView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.black.opacity(0.1))
                .previewDisplayName("Confetti Animation Test")
        }
    }
}
#endif

