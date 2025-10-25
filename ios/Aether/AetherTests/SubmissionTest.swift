import Testing
import SwiftData
import Foundation
@testable import Aether


@Suite("Quiz Submission Tests")
struct QuizSubmissionTests {
    
    @Test("Test building submission answers from QuizAttempt")
    func testBuildSubmissionAnswers() async throws {
        // 创建模拟的网络服务和模型上下文
        let mockNetwork = MockNetworkService()
        let mockContext = try await ModelContainer(
            for: QuizAttempt.self, StoredQuestion.self,
            configurations: .init(isStoredInMemoryOnly: true)
        ).mainContext
        
        let viewModel = await QuizViewModel(network: mockNetwork, modelContext: mockContext)
        
        // 创建测试用的QuizAttempt
        let attempt = QuizAttempt(
            attemptId: UUID(),
            userId: UUID(),
            courseId: "test-course",
            questionNum: 2,
            status: .completed,
            createdAt: Date()
        )
        
        // 创建多选题
        let mcqQuestion = StoredQuestion(
            id: UUID(),
            text: "What is 2+2?",
            type: .multipleChoice,
            detailsJSON: """
            {
                "options": ["3", "4", "5", "6"],
                "correct_answer": 1
            }
            """,
            isSubmitted: true,
            selectedOptionIndex: 1
        )
        
        // 创建填空题
        let fillBlankQuestion = StoredQuestion(
            id: UUID(),
            text: "Fill in the blank",
            type: .fillInTheBlank,
            detailsJSON: """
            {
                "expected_answer": ["answer1", "answer2"]
            }
            """,
            isSubmitted: true,
            userTextAnswer: "answer1"
        )
        
        attempt.questions = [mcqQuestion, fillBlankQuestion]
        
        // 测试构建提交答案
        let answers = await viewModel.buildSubmissionAnswers(from: attempt)
        
        #expect(answers.count == 2, "Should have 2 submitted answers")
        
        // 验证多选题答案
        let mcqAnswer = answers.first { $0.questionId == mcqQuestion.id }
        #expect(mcqAnswer != nil, "MCQ answer should exist")
        
        if case .multipleChoice(let mcqAnswerData) = mcqAnswer?.answer {
            #expect(mcqAnswerData.selectedOption == 1, "Selected option should be 1")
        } else {
            #expect(Bool(false), "MCQ answer should be multiple choice type")
        }
        
        // 验证填空题答案
        let fillAnswer = answers.first { $0.questionId == fillBlankQuestion.id }
        #expect(fillAnswer != nil, "Fill blank answer should exist")
        
        if case .fillInTheBlank(let fillAnswerData) = fillAnswer?.answer {
            #expect(fillAnswerData.textAnswer == "answer1", "Text answer should be 'answer1'")
        } else {
            #expect(Bool(false), "Fill blank answer should be fill in the blank type")
        }
    }
    
    @Test("Test QuizSubmissionRequest JSON encoding")
    func testSubmissionRequestEncoding() async throws {
        let mcqAnswer = AnyAnswer.multipleChoice(
            MultipleChoiceAnswer(selectedOption: 2)
        )
        
        let fillAnswer = AnyAnswer.fillInTheBlank(
            FillInTheBlankAnswer(textAnswer: "test answer")
        )
        
        let answers = [
            ClientAnswerInput(questionId: UUID(), answer: mcqAnswer),
            ClientAnswerInput(questionId: UUID(), answer: fillAnswer)
        ]
        
        let request = QuizSubmissionRequest(answers: answers)
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(request)
        let jsonString = String(data: data, encoding: .utf8)
        
        #expect(jsonString != nil, "Should be able to encode to JSON")
        #expect(jsonString!.contains("multiple_choice"), "Should contain question type")
        #expect(jsonString!.contains("selected_option"), "Should contain selected option")
        #expect(jsonString!.contains("fill_in_the_blank"), "Should contain fill blank type")
        #expect(jsonString!.contains("text_answer"), "Should contain text answer")
    }
    
    @Test("Test QuizSubmissionEndpoint configuration")
    func testSubmissionEndpoint() {
        let submissionId = UUID()
        let request = QuizSubmissionRequest(answers: [])
        
        let endpoint = QuizSubmissionEndpoint(
            submissionId: submissionId,
            submissionRequest: request
        )
        
        #expect(endpoint.path == "/submissions/\(submissionId)", "Path should be correct")
        #expect(endpoint.method == .POST, "Method should be POST")
        #expect(endpoint.requiredAuth == true, "Should require authentication")
        
        // 验证请求体
        if case .json(let body) = endpoint.body {
            #expect(body is QuizSubmissionRequest, "Body should be QuizSubmissionRequest")
        } else {
            #expect(Bool(false), "Should have JSON body")
        }
    }
}

