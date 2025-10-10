import Foundation
import Combine

@MainActor
class QuizViewModel: ObservableObject {
    // MARK: - Published Properties
    // TODO: I still need to know how to get the problems from last viewmodel
    let problems: [QuizProblem]
    
    @Published var currentProblemIndex = 0
    @Published var selectedOptionIndex: Int?
    @Published var isAnswerSubmitted = false
    
    @Published var score = 0
    
    init(problems: [QuizProblem]) {
        self.problems = problems
    }
    
    var currentQuestion: QuizProblem? {
        guard currentProblemIndex < problems.count else { return nil }
        return problems[currentProblemIndex]
    }

    var isQuizFinished: Bool {
        return currentProblemIndex >= problems.count
    }
    
    func submitAnswer() {
        guard let selectedIndex = self.selectedOptionIndex,
              let question = currentQuestion else{
            return
        }
        if self.selectedOptionIndex == question.correctAnswerIndex {
            self.score += 1
        }
        isAnswerSubmitted = true
    }
    
    func nextQuestion() {
        if self.currentProblemIndex < problems.count - 1 {
            self.currentProblemIndex += 1
            resetForNextQuesion()
        } else {
            self.currentProblemIndex += 1
        }
    }
    
    func resetForNextQuesion() {
        selectedOptionIndex = nil
        isAnswerSubmitted = false
    }
    
    func restartQuiz() {
        score = 0
        currentProblemIndex = 0
        resetForNextQuesion()
    }
}
