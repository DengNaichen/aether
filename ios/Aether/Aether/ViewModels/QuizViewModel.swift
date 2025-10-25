import Foundation
import Combine

@MainActor
class QuizViewModel: ObservableObject, NetworkViewModeling {
    private let network: NetworkServicing
    
    @Published var isLoading: Bool = false
    @Published var alertItem: AlertItem?
    @Published var questions: [mcqQuestion] = []
    @Published var currentQuestionIndex = 0
    @Published var selectedOptionIndex: Int?
    @Published var isAnswerSubmitted = false
    @Published var score = 0
    
 

    init(network: NetworkService) {
        self.network = network
    }
    
    
    func startQuiz(courseId: String, questionNum: Int) async {
        
        self.questions = []
        
        let response = await performTask(errorTitle: "Quiz Start Failed") {
            
            let request = QuizStartRequest(questionNum: questionNum)
            let endpoint = QuizStartEndpoint(courseId: courseId)
            return try await network.request(
                endpoint: endpoint, responseType: QuizStartResponse.self)
        }
        if let response {
            self.questions = mapToUIQuestion(from: response.questions)
        }
    }
    
    private func mapToUIQuestion(from responseQuestions: [AnyQuestion])
    -> [mcqQuestion] {
        var uiQuestion: [mcqQuestion] = []
        for responseQuestion in responseQuestions {
            if case .multipleChoice(let mcq) = responseQuestion {
                let question = mcqQuestion(
                    id: mcq.id,
                    text: mcq.text,
                    options: mcq.details.options,
                    correctAnswerIndex: mcq.details.correctAnswer
                )
                uiQuestion.append(question)
            }
        }
        return uiQuestion
    }
    
    var currentQuestion: mcqQuestion? {
        guard currentQuestionIndex < questions.count else { return nil }
        return questions[currentQuestionIndex]
    }

    var isQuizFinished: Bool {
        return currentQuestionIndex >= questions.count
    }

    func submitQuestionAnswer() {
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
        if self.currentQuestionIndex < questions.count - 1 {
            self.currentQuestionIndex += 1
            resetForNextQuesion()
        } else {
            self.currentQuestionIndex += 1
        }
    }
    
    func resetForNextQuesion() {
        selectedOptionIndex = nil
        isAnswerSubmitted = false
    }
    
    func submissionQuiz() {
        
    }
}
