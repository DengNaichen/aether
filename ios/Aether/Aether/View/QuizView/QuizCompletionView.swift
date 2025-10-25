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
                
                Text("\(viewModel.score) / \(viewModel.questions.count)")
                    .font(.system(size: 60, weight: .bold))
                
                Button(action: {
                    viewModel.submitQuiz()
                }) {
                    Text("submit")
                        .font(.headline)
                        .fontWeight(.bold)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }
        }
        .onAppear {
            showConfetti = true
            triggerHapticFeedback()
        }
    }

    private func triggerHapticFeedback() {
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.success)
    }
}

#if DEBUG
//struct QuizCompletionView_Previews: PreviewProvider {
//    static var previews: some View {
//        // Create a mock QuizViewModel for the preview
//        let viewModel = QuizViewModel(
//            network: MockNetworkService(),
//            modelContext: try! ModelContainer(for: Course.self, QuizAttempt.self).mainContext
//        )
//        viewModel.score = 8
//        viewModel.questions = [
//            QuestionDisplay(from: Question(id: "q1", text: "Q1", options: [], answer: "A", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q2", text: "Q2", options: [], answer: "B", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q3", text: "Q3", options: [], answer: "C", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q4", text: "Q4", options: [], answer: "D", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q5", text: "Q5", options: [], answer: "A", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q6", text: "Q6", options: [], answer: "B", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q7", text: "Q7", options: [], answer: "C", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q8", text: "Q8", options: [], answer: "D", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q9", text: "Q9", options: [], answer: "A", quizId: "1")),
//            QuestionDisplay(from: Question(id: "q10", text: "Q10", options: [], answer: "B", quizId: "1")),
//        ]
//        
//        return QuizCompletionView(viewModel: viewModel)
//    }
//}
#endif

