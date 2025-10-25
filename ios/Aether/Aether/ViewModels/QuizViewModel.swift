import Foundation
import Combine
import SwiftData

@MainActor
class QuizViewModel: ObservableObject, NetworkViewModeling {
    private let network: NetworkServicing
    private let modelContext: ModelContext
    
    @Published var activeAttempt: QuizAttempt?
    
    @Published var isLoading: Bool = false
    @Published var alertItem: AlertItem?
    @Published var questions: [QuestionDisplay] = []
    @Published var score = 0
    
    // This is the UI state, which we will sync with activeAttempt
    @Published var currentQuestionIndex: Int = 0
    @Published var selectedOptionIndex: Int?
    @Published var userTextAnswer: String = ""
    @Published var isAnswerSubmitted: Bool = false
    

    init(network: NetworkServicing, modelContext: ModelContext) {
        self.network = network
        self.modelContext = modelContext
    }
    
    var isQuizFinished: Bool {
        activeAttempt?.status == .completed
    }
    
    var currentQuestion: QuestionDisplay? {
        guard !questions.isEmpty,
              currentQuestionIndex >= 0,
              currentQuestionIndex < questions.count else {
            return nil
        }
        return questions[currentQuestionIndex]
    }
    
    
    func startQuiz(courseId: String, questionNum: Int) async {
        isLoading = true
        defer { isLoading = false }
        
        // try to get from the local database
        if let exisitingAttempt = fetchInProgressQuiz(courseId: courseId) {
            print("Find a unfinished quiz, resuming ...")
            
            self.activeAttempt = exisitingAttempt
            self.questions = exisitingAttempt.questions.map{
                QuestionDisplay(from: $0)
            }
            self.currentQuestionIndex = exisitingAttempt.currentQuestionIndex
            
        } else {
            print("No unfinished quiz found, starting a new one from server")
            
            guard let quizResponse = await fetchQuizFromServer(
                courseId: courseId, questionNum: questionNum) else {
                return // fetchQuizFromServer will set alertItem
            }
            
            let newAttempt = QuizAttempt(from: quizResponse)
            modelContext.insert(newAttempt)
            
            self.activeAttempt = newAttempt
            self.questions = newAttempt.questions
                .map{ QuestionDisplay(from: $0) }
            
            self.currentQuestionIndex = newAttempt.currentQuestionIndex
        }
        loadStateForCurrentQuestion()
    }
    
    func submitAnswer() {
        guard let attempt = activeAttempt else { return }
        
        let currentQuestionDisplay = questions[currentQuestionIndex]
        
        guard let storedQuestion = attempt.questions.first(
            where: { $0.id == currentQuestionDisplay.id }) else {
            print("Error: Cannot find the submitted the storedQuestion")
            return
        }
        
        if storedQuestion.isSubmitted { return }
        
        storedQuestion.isSubmitted = true
        
        var isCorrect = false
        
        switch currentQuestionDisplay.details {
        case .multipleChoice(let details):
            storedQuestion.selectedOptionIndex = self.selectedOptionIndex
            if selectedOptionIndex == details.correctAnswer {
                isCorrect = true
            }
            
        case .fillInTheBlank(let details):
            let answer = self.userTextAnswer.trimmingCharacters(in: .whitespaces)
            storedQuestion.userTextAnswer = answer
            if details.expectedAnswer.contains(where: {
                $0.caseInsensitiveCompare(answer) == .orderedSame }) {
                isCorrect = true
            }
            
        case .calculation(let details):
            let answer = self.userTextAnswer.trimmingCharacters(in: .whitespaces)
            storedQuestion.userTextAnswer = answer
            if details.expectedAnswer.contains(answer) {
                isCorrect = true
            }
        }
        
        if isCorrect {
            attempt.score += 1
            self.score = attempt.score
        }
        
        self.isAnswerSubmitted = true
        
        questions[currentQuestionIndex] = QuestionDisplay(from: storedQuestion)
    }
    
    
    private func loadStateForCurrentQuestion() {
        guard let attempt = activeAttempt,
              !questions.isEmpty,
              currentQuestionIndex >= 0,
              currentQuestionIndex < questions.count else {
            // Reset state if we can't load
            self.selectedOptionIndex = nil
            self.userTextAnswer = ""
            self.isAnswerSubmitted = false
            return
        }
        
        let currentQuestion = questions[currentQuestionIndex]
        
        // Load the saved state for this question
        self.isAnswerSubmitted = currentQuestion.isSubmitted
        self.selectedOptionIndex = currentQuestion.selectedOptionIndex
        self.userTextAnswer = currentQuestion.userTextAnswer ?? ""
    }
    
    private func fetchInProgressQuiz(courseId: String) -> QuizAttempt? {
        let inProgressStatus = QuizStatus.inProgress.rawValue
        
        let predicate = #Predicate<QuizAttempt> { attempt in
            attempt.courseId == courseId &&
            attempt.statusRawValue == inProgressStatus
        }
        var descriptor = FetchDescriptor<QuizAttempt>(predicate: predicate)
        descriptor.sortBy = [SortDescriptor(\.createdAt, order: .reverse)]
        descriptor.fetchLimit = 1
        
        do {
            let attempts = try modelContext.fetch(descriptor)
            return attempts.first
        } catch {
            print("Fetch in progress quiz failed.")
            return nil
        }
    }
    
    private func fetchQuizFromServer(courseId: String, questionNum: Int) async
    -> QuizResponse? {
        let response = await performTask(errorTitle: "Quiz Start Failed") {
            
            let endpoint = QuizStartEndpoint(courseId: courseId, questionNum: questionNum)
            return try await network.request(
                endpoint: endpoint, responseType: QuizResponse.self)
        }
        if let response {
            return response
        }
        return nil
    }
    

    func advanceToNextQuestion() {
        guard let attempt = activeAttempt else { return }
        
        if currentQuestionIndex < questions.count - 1 {
            currentQuestionIndex += 1
            attempt.currentQuestionIndex = self.currentQuestionIndex
            
            loadStateForCurrentQuestion()
        } else {
            attempt.status = .completed
            // TODO: Here will triger the upload to server login, and navigate
            // to result page
        }
    }
    func submitQuiz() async {
        guard let attempt = activeAttempt else {
            alertItem = AlertItem(
                title: "提交失败",
                message: "未找到有效的测验记录"
            )
            return
        }
        
        // 确保测验状态为已完成
        attempt.status = .completed
        
        isLoading = true
        defer { isLoading = false }
        
        // 构建提交答案
        let answers = buildSubmissionAnswers(from: attempt)
        let submissionRequest = QuizSubmissionRequest(answers: answers)
        
        // 提交到服务器
        let success = await submitToServer(
            submissionId: attempt.attemptId,
            request: submissionRequest
        )
        
        if success {
            // 保存到本地数据库，确保状态已更新
            do {
                try modelContext.save()
                print("✅ 测验提交成功并保存到本地")
            } catch {
                print("❌ 保存到本地失败: \(error)")
                alertItem = AlertItem(
                    title: "保存失败",
                    message: "测验已提交但本地保存失败"
                )
            }
        } else {
            // 如果提交失败，将状态改回进行中
            attempt.status = .inProgress
        }
    }
    
    internal func buildSubmissionAnswers(from attempt: QuizAttempt) -> [ClientAnswerInput] {
        return attempt.questions.compactMap { storedQuestion in
            guard storedQuestion.isSubmitted else { return nil }
            
            let answer: AnyAnswer
            
            switch storedQuestion.questionType {
            case .multipleChoice:
                guard let selectedIndex = storedQuestion.selectedOptionIndex else {
                    print("⚠️ 多选题没有选择答案: \(storedQuestion.id)")
                    return nil
                }
                answer = .multipleChoice(MultipleChoiceAnswer(selectedOption: selectedIndex))
                
            case .fillInTheBlank:
                guard let textAnswer = storedQuestion.userTextAnswer,
                      !textAnswer.trimmingCharacters(in: .whitespaces).isEmpty else {
                    print("⚠️ 填空题没有答案: \(storedQuestion.id)")
                    return nil
                }
                answer = .fillInTheBlank(FillInTheBlankAnswer(textAnswer: textAnswer))
                
            case .calculation:
                guard let textAnswer = storedQuestion.userTextAnswer,
                      !textAnswer.trimmingCharacters(in: .whitespaces).isEmpty else {
                    print("⚠️ 计算题没有答案: \(storedQuestion.id)")
                    return nil
                }
                answer = .calculation(CalculationAnswer(numericAnswer: textAnswer))
            }
            
            return ClientAnswerInput(questionId: storedQuestion.id, answer: answer)
        }
    }
    
    private func submitToServer(submissionId: UUID, request: QuizSubmissionRequest) async -> Bool {
        let response = await performTask(
            errorTitle: "提交失败",
            task: {
                let endpoint = QuizSubmissionEndpoint(
                    submissionId: submissionId,
                    submissionRequest: request
                )
                return try await network.request(
                    endpoint: endpoint,
                    responseType: QuizSubmissionResponse.self
                )
            }
        )
        
        if let response = response {
            print("✅ 测验提交成功: \(response.message)")
            return true
        } else {
            return false
        }
    }
}
