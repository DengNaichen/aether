import Testing
import Foundation
import SwiftData
@testable import Aether

extension QuizAttempt {
    static func makeMock(
        attemptId: UUID = UUID(),
        userId: UUID = UUID(),
        courseId: String = "CS101",
        questionNum: Int = 3,
        status: QuizStatus = .inProgress,
        createdAt: Date = Date()
    ) -> QuizAttempt {
        QuizAttempt(
            attemptId: attemptId,
            userId: userId,
            courseId: courseId,
            questionNum: questionNum,
            status: status,
            createdAt: createdAt
        )
    }
}

extension StoredQuestion {
    static func makeMockMultipleChoice(
        id: UUID = UUID(),
        text: String = "What is 2+2?"
    ) -> StoredQuestion {
        let details = MultipleChoiceDetails(
            options: ["1", "2", "3", "4"],
            correctAnswer: 3
        )
        let detailsJSON = try! String(
            data: JSONEncoder().encode(details),
            encoding: .utf8
        )!
        
        return StoredQuestion(
            id: id,
            text: text,
            type: .multipleChoice,
            detailsJSON: detailsJSON
        )
    }
    
    static func makeMockFillInBlank(
        id: UUID = UUID(),
        text: String = "The capital of France is ___"
    ) -> StoredQuestion {
        let details = FillInTheBlankDetails(
            expectedAnswer: ["Paris"]
//            correctAnswer: "Paris"
        )
        let detailsJSON = try! String(
            data: JSONEncoder().encode(details),
            encoding: .utf8
        )!
        
        return StoredQuestion(
            id: id,
            text: text,
            type: .fillInTheBlank,
            detailsJSON: detailsJSON
        )
    }
    static func makeMockCalculation(
        id: UUID = UUID(),
        text: String = "What is 3 * 7?"
    ) -> StoredQuestion {
        let details = CalculationDetails(
            expectedAnswer: ["21"],
            precision: 0
        )
        let detailsJSON = try! String(
            data: JSONEncoder().encode(details),
            encoding: .utf8
        )!
        
        return StoredQuestion(
            id: id,
            text: text,
            type: .calculation,
            detailsJSON: detailsJSON
        )
    }
}

// MARK: - QuizAttempt Tests
@Suite("QuizAttempt Tests")
struct QuizAttemptTests {
    
    @Test("Initialize QuizAttempt with basic properties")
    func testInitialization() {
        let attemptId = UUID()
        let userId = UUID()
        let createdAt = Date()
        
        let attempt = QuizAttempt(
            attemptId: attemptId,
            userId: userId,
            courseId: "CS101",
            questionNum: 5,
            status: .inProgress,
            createdAt: createdAt
        )
        
        #expect(attempt.attemptId == attemptId)
        #expect(attempt.userId == userId)
        #expect(attempt.courseId == "CS101")
        #expect(attempt.questionNum == 5)
        #expect(attempt.status == .inProgress)
        #expect(attempt.createdAt == createdAt)
        #expect(attempt.questions.isEmpty)
    }
    
    @Test("QuizStatus enum conversion")
    func testStatusConversion() {
        let attempt = QuizAttempt.makeMock(status: .inProgress)
        
        #expect(attempt.status == .inProgress)
        #expect(attempt.statusRawValue == QuizStatus.inProgress.rawValue)
        
        // Change status
        attempt.status = .completed
        #expect(attempt.status == .completed)
        #expect(attempt.statusRawValue == QuizStatus.completed.rawValue)
    }
    
//    @Test("Initialize from QuizResponse")
//    func testInitFromResponse() {
//        let response = QuizResponse(
//            attemptId: UUID(),
//            userId: UUID(),
//            courseId: "MATH202",
//            questionNum: 3,
//            status: .inProgress,
//            createdAt: Date(),
//            questions: [
//                .multipleChoice(MultipleChoiceQuestion(
//                    id: UUID(),
//                    text: "Question 1",
//                    details: MultipleChoiceDetails(
//                        options: ["A", "B", "C"],
//                        correctAnswer: 0
//                    )
//                ))
//            ]
//        )
//        
//        let attempt = QuizAttempt(from: response)
//        
//        #expect(attempt.attemptId == response.attemptId)
//        #expect(attempt.userId == response.userId)
//        #expect(attempt.courseId == "MATH202")
//        #expect(attempt.questionNum == 3)
//        #expect(attempt.questions.count == 1)
//    }
    
    @Test("Invalid status defaults to inProgress")
    func testInvalidStatusHandling() {
        let attempt = QuizAttempt.makeMock()
        attempt.statusRawValue = "INVALID_STATUS"
        
        #expect(attempt.status == .inProgress)
    }
}

// MARK: - StoredQuestion Tests
@Suite("StoredQuestion Tests")
struct StoredQuestionTests {
    
    @Test("Initialize StoredQuestion with basic properties")
    func testInitialization() {
        let id = UUID()
        let question = StoredQuestion(
            id: id,
            text: "Test question",
            type: .multipleChoice,
            detailsJSON: "{}"
        )
        
        #expect(question.id == id)
        #expect(question.text == "Test question")
        #expect(question.questionType == .multipleChoice)
        #expect(question.detailsJSON == "{}")
        #expect(question.quizAttemp == nil)
    }
}

// MARK: - QuizDisplay Tests
@Suite("QuizDisplay Tests")
struct QuizDisplayTests {
    
    @Test("Initialize from QuizAttempt")
    func testInitFromQuizAttempt() {
        let attemptId = UUID()
        let createdAt = Date()
        let attempt = QuizAttempt(
            attemptId: attemptId,
            userId: UUID(),
            courseId: "CS101",
            questionNum: 3,
            status: .inProgress,
            createdAt: createdAt,
            questions: [
                StoredQuestion.makeMockMultipleChoice(),
                StoredQuestion.makeMockFillInBlank(),
                StoredQuestion.makeMockCalculation()
            ]
        )
        
        let displayModel = QuizDisplay(from: attempt)
        
        #expect(displayModel.id == attemptId)
        #expect(displayModel.courseId == "CS101")
        #expect(displayModel.questionCount == 3)
        #expect(displayModel.status == .inProgress)
        #expect(displayModel.createdAt == createdAt)
        #expect(displayModel.questions.count == 3)
    }
    @Test("Initialize from QuizAttempt with no questions")
    func testInitFromQuizAttemptWithNoQuestions() {
        let attempt = QuizAttempt.makeMock(questionNum: 0)
        
        let displayModel = QuizDisplay(from: attempt)
        
        #expect(displayModel.questions.isEmpty)
        #expect(displayModel.questionCount == 0)
    }
    
    @Test("QuizDisplay is Identifiable")
    func testIdentifiable() {
        let attempt = QuizAttempt.makeMock()
        let displayModel = QuizDisplay(from: attempt)
        
        #expect(displayModel.id == attempt.attemptId)
    }
    
    @Test("QuizDisplay is Equatable")
    func testEquatable() {
        let attempt1 = QuizAttempt.makeMock(attemptId: UUID())
        let attempt2 = QuizAttempt.makeMock(attemptId: UUID())
        
        let model1 = QuizDisplay(from: attempt1)
        let model2 = QuizDisplay(from: attempt1)
        let model3 = QuizDisplay(from: attempt2)
        
        #expect(model1 == model2)
        #expect(model1 != model3)
    }
}

// MARK: - QuestionDisplay Tests
@Suite("QuestionDisplay Tests")
struct QuestionDisplayTests {
    
    @Test("Initialize from MultipleChoice StoredQuestion")
    func testInitFromMCStoredQuestion() {
        let questionId = UUID()
        let stored = StoredQuestion.makeMockMultipleChoice(
            id: questionId,
            text: "Test question"
        )
        
        let displayModel = QuestionDisplay(from: stored)
        
        #expect(displayModel.id == questionId)
        #expect(displayModel.text == "Test question")
        
        guard case .multipleChoice(let details) = displayModel.details else {
            Issue.record("Wrong question details type")
            return
        }
        #expect(details.options.count == 4)
        #expect(details.correctAnswer == 3)
    }
    
    @Test("Initialize from FillInTheBlank StoredQuestion")
    func testInitFromFIBStoredQuestion() {
        let questionId = UUID()
        let stored = StoredQuestion.makeMockFillInBlank(
            id: questionId,
            text: "FIB question"
        )
        
        let displayModel = QuestionDisplay(from: stored)
        
        #expect(displayModel.id == questionId)
        #expect(displayModel.text == "FIB question")
        
        guard case .fillInTheBlank(let details) = displayModel.details else {
            Issue.record("Wrong question details type")
            return
        }
        #expect(details.expectedAnswer == ["Paris"])
    }
    
    @Test("Initialize from Calculation StoredQuestion")
    func testInitFromCalcStoredQuestion() {
        let questionId = UUID()
        let stored = StoredQuestion.makeMockCalculation(
            id: questionId,
            text: "Calc question"
        )
        
        let displayModel = QuestionDisplay(from: stored)
        
        #expect(displayModel.id == questionId)
        #expect(displayModel.text == "Calc question")
        
        guard case .calculation(let details) = displayModel.details else {
            Issue.record("Wrong question details type")
            return
        }
        #expect(details.expectedAnswer == ["21"])
        #expect(details.precision == 0)
    }
    
    @Test("QuestionDisplay is Identifiable")
    func testIdentifiable() {
        let stored = StoredQuestion.makeMockMultipleChoice()
        let displayModel = QuestionDisplay(from: stored)
        
        #expect(displayModel.id == stored.id)
    }
    
    @Test("QuestionDisplay is Equatable")
    func testEquatable() {
        let stored1 = StoredQuestion.makeMockMultipleChoice(id: UUID())
        let stored2 = StoredQuestion.makeMockMultipleChoice(id: UUID())
        
        let model1 = QuestionDisplay(from: stored1)
        let model2 = QuestionDisplay(from: stored1)
        let model3 = QuestionDisplay(from: stored2)
        
        #expect(model1 == model2)
        #expect(model1 != model3)
    }
}

    @Test("Initialization fails with invalid JSON")
    func testInitWithInvalidJSON() {
        let stored = StoredQuestion(
            id: UUID(),
            text: "Test",
            type: .multipleChoice,
            detailsJSON: "invalid json"
        )
        
        #expect(throws: (any Error).self) {
            _ = QuestionDisplay(from: stored)
        }
    }

    @Test("Initialization fails with mismatched JSON")
    func testInitWithMismatchedJSON() {
        let details = FillInTheBlankDetails(
            expectedAnswer: ["Paris"]
        )
        let detailsJSON = try! String(
            data: JSONEncoder().encode(details),
            encoding: .utf8
        )!
        
        let stored = StoredQuestion(
            id: UUID(),
            text: "Test",
            type: .multipleChoice, // Mismatched type
            detailsJSON: detailsJSON
        )
        
        #expect(throws: (any Error).self) {
            _ = QuestionDisplay(from: stored)
        }
    }

    @Test("Initialization fails with empty JSON")
    func testInitWithEmptyJSON() {
        let stored = StoredQuestion(
            id: UUID(),
            text: "Test",
            type: .multipleChoice,
            detailsJSON: "{}"
        )
        
        #expect(throws: (any Error).self) {
            _ = QuestionDisplay(from: stored)
        }
    }
