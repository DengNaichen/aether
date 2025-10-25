import Foundation
import SwiftData

// MARK: - 1. Network layer (From Server)
struct QuizStartEndpoint: Endpoint {
    let courseId: String
    
    var path: String { "/courses/\(courseId)/quizzes" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(QuizRequest(questionNum: 2)) }
    var requiredAuth: Bool { true }
}

enum QuizStatus: String, Codable {
    case inProgress = "IN_PROGRESS"
    case completed = "COMPLETED"
    case aborted = "ABORTED"
}

struct QuizRequest: Codable {
    let questionNum: Int
    
    enum CodingKeys: String, CodingKey {
        case questionNum = "question_num"
    }
}

struct QuizResponse: Codable {
    let attemptId: UUID
    let userId: UUID
    let courseId: String
    let questionNum: Int
    let status: QuizStatus
    let createdAt: Date
    let questions: [AnyQuestion]
    
    enum CodingKeys: String, CodingKey {
        case attemptId = "attempt_id"
        case userId = "user_id"
        case courseId = "course_id"
        case questionNum = "question_num"
        case status = "status"
        case createdAt = "created_at"
        case questions = "questions"
    }
}


// MARK: - Data persistence layer
@Model
final class QuizAttempt {
    @Attribute(.unique) var attemptId: UUID
    var userId: UUID
    var courseId: String
    var questionNum: Int
    var statusRawValue: String
    var createdAt: Date
    
    var currentQuestionIndex: Int
    var score: Int
    
    @Relationship(deleteRule: .cascade, inverse: \StoredQuestion.quizAttempt)
    var questions: [StoredQuestion]
    
    var status: QuizStatus {
        get { QuizStatus(rawValue: statusRawValue) ?? .inProgress }
        set { statusRawValue = newValue.rawValue }
    }
    
    init(attemptId: UUID, userId: UUID, courseId: String, questionNum: Int,
         status: QuizStatus, createdAt: Date, questions: [StoredQuestion] = [],
         currentQuestionIndex: Int = 0, score: Int = 0) {
        self.attemptId = attemptId
        self.userId = userId
        self.courseId = courseId
        self.questionNum = questionNum
        self.statusRawValue = status.rawValue
        self.createdAt = createdAt
        self.questions = questions
        
        self.currentQuestionIndex = currentQuestionIndex
        self.score = score
    }
    
    @MainActor
    convenience init(from response: QuizResponse) {
        self.init(
            attemptId: response.attemptId,
            userId: response.userId,
            courseId: response.courseId,
            questionNum: response.questionNum,
            status: response.status,
            createdAt: response.createdAt,
            currentQuestionIndex: 0,
            score: 0
        )
        self.questions = response.questions.map {
            StoredQuestion(from: $0, quizAttempt: self)
        }
    }
}

@Model
final class StoredQuestion {
    @Attribute(.unique) var id: UUID
    var text: String
    var typeRawValue: String
    var detailsJSON: String
    
    var isSubmitted: Bool
    var selectedOptionIndex: Int? // for choice question
    var userTextAnswer: String? // for fillin and calculation
    
    var quizAttempt: QuizAttempt?
    
    var questionType: QuestionType {
        QuestionType(rawValue: typeRawValue) ?? .multipleChoice
    }
    
    init(id: UUID, text: String, type: QuestionType, detailsJSON: String,
         isSubmitted: Bool = false,
         selectedOptionIndex: Int? = nil,
         userTextAnswer: String? = nil) {
        self.id = id
        self.text = text
        self.typeRawValue = type.rawValue
        self.detailsJSON = detailsJSON
        
        self.isSubmitted = isSubmitted
        self.selectedOptionIndex = selectedOptionIndex
        self.userTextAnswer = userTextAnswer
    }
    
    @MainActor
    convenience init(from anyQuestion: AnyQuestion, quizAttempt: QuizAttempt) {
        let encoder = JSONEncoder()
        let detailsJSON: String
        
        switch anyQuestion {
        case .multipleChoice(let q):
            detailsJSON = (try? String(data: encoder.encode(q.details),
                                       encoding: .utf8)) ?? "{}"
        case .fillInTheBlank(let q):
            detailsJSON = (try? String(data: encoder.encode(q.details),
                                       encoding: .utf8)) ?? "{}"
        case .calculation(let q):
            detailsJSON = (try? String(data: encoder.encode(q.details),
                                       encoding: .utf8)) ?? "{}"
        }
        
        self.init(
            id: anyQuestion.id,
            text: anyQuestion.text,
            type: anyQuestion.questionType,
            detailsJSON: detailsJSON
        )
        self.quizAttempt = quizAttempt
    }
}

// MARK: - View/ViewModel layer (For UI Display)

struct QuizDisplay: Identifiable, Equatable {
    let id: UUID
    let courseId: String
    let questionCount: Int
    let status: QuizStatus
    let createdAt: Date
    let questions: [QuestionDisplay]
    
    init(from attempt: QuizAttempt) {
        self.id = attempt.attemptId
        self.courseId = attempt.courseId
        self.questionCount = attempt.questionNum
        self.status = attempt.status
        self.createdAt = attempt.createdAt
        self.questions = attempt.questions.map { QuestionDisplay(from: $0) }
    }
}

struct QuestionDisplay: Identifiable, Equatable {
    let id: UUID
    let text: String
    let details: QuestionDetailsDisplay
    
    let isSubmitted: Bool
    let selectedOptionIndex: Int?
    let userTextAnswer: String?
    
    init(from stored: StoredQuestion) {
        self.id = stored.id
        self.text = stored.text
        
        self.isSubmitted = stored.isSubmitted
        self.selectedOptionIndex = stored.selectedOptionIndex
        self.userTextAnswer = stored.userTextAnswer
        
        let decoder = JSONDecoder()
        guard let data = stored.detailsJSON.data(using: .utf8) else {
            fatalError("Failed to convert detailsJSON to Data")
        }
        
        switch stored.questionType {
        case .multipleChoice:
            do {
                let details = try decoder.decode(MultipleChoiceDetails.self, from: data)
                self.details = .multipleChoice(
                    .init(options: details.options, correctAnswer: details.correctAnswer)
                )
            } catch {
                fatalError("Failed to decode MultipleChoiceDetails: \(error)")
            }
        case .fillInTheBlank:
            do {
                let details = try decoder.decode(FillInTheBlankDetails.self, from: data)
                self.details = .fillInTheBlank(
                    .init(expectedAnswer: details.expectedAnswer)
                )
            } catch {
                fatalError("Failed to decode FillInTheBlankDetails: \(error)")
            }
        case .calculation:
            do {
                let details = try decoder.decode(CalculationDetails.self, from: data)
                self.details = .calculation(
                    .init(expectedAnswer: details.expectedAnswer, precision: details.precision)
                )
            } catch {
                fatalError("Failed to decode CalculationDetails: \(error)")
            }
        }
    }
}

