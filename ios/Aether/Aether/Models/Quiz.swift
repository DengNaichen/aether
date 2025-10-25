import Foundation
import SwiftData

// MARK: - Network layer
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
    
    @Relationship(deleteRule: .cascade, inverse: \StoredQuestion.quizAttemp)
    var questions: [StoredQuestion]
    
    var status: QuizStatus {
        get { QuizStatus(rawValue: statusRawValue) ?? .inProgress }
        set { statusRawValue = newValue.rawValue }
    }
    
    init(attemptId: UUID, userId: UUID, courseId: String,
         questionNum: Int, status: QuizStatus, createdAt: Date,
         questions: [StoredQuestion] = []) {
        self.attemptId = attemptId
        self.userId = userId
        self.courseId = courseId
        self.questionNum = questionNum
        self.statusRawValue = status.rawValue
        self.createdAt = createdAt
        self.questions = questions
    }
    
    convenience init(from response: QuizResponse) {
        self.init(
            attemptId: response.attemptId,
            userId: response.userId,
            courseId: response.courseId,
            questionNum: response.questionNum,
            status: response.status,
            createdAt: response.createdAt
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
    
    var quizAttemp: QuizAttempt?
    
    var questionType: QuestionType {
        QuestionType(rawValue: typeRawValue) ?? .multipleChoice
    }
    
    init(id: UUID, text: String, type: QuestionType, detailsJSON: String) {
        self.id = id
        self.text = text
        self.typeRawValue = type.rawValue
        self.detailsJSON = detailsJSON
    }
    
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
        self.quizAttemp = quizAttempt
    }
}

// MARK: - View and ViewModel layer
struct QuizDisplayModel: Identifiable, Equatable {
    let id: UUID
    let courseId: String
    let questionCount: Int
    let status: QuizStatus
    let createdAt: Date
    let questions: [QuestionDisplayModel]
    
    init(from attempt: QuizAttempt) {
        self.id = attempt.attemptId
        self.courseId = attempt.courseId
        self.questionCount = attempt.questionNum
        self.status = attempt.status
        self.createdAt = attempt.createdAt
        self.questions = attempt.questions.map { QuestionDisplayModel(from: $0) }
        
    }
}

struct QuestionDisplayModel: Identifiable, Equatable {
    let id: UUID
    let text: String
    let type: QuestionType
    let detailsJSON: String
    
    init(from stored: StoredQuestion) {
        self.id = stored.id
        self.text = stored.text
        self.type = stored.questionType
        self.detailsJSON = stored.detailsJSON
        
        var multipleChoiceDetails: MultipleChoiceDetails? {
            guard type == .multipleChoice,
                  let data = detailsJSON.data(using: .utf8) else { return nil }
            return try? JSONDecoder().decode(MultipleChoiceDetails.self, from: data)
        }
        
        var fillInTheBlankDetails: FillInTheBlankDetails? {
            guard type == .fillInTheBlank,
                  let data = detailsJSON.data(using: .utf8) else { return nil }
            return try? JSONDecoder().decode(FillInTheBlankDetails.self, from: data)
        }
        
        var calculationDetails: CalculationDetails? {
            guard type == .calculation,
                  let data = detailsJSON.data(using: .utf8) else { return nil }
            return try? JSONDecoder().decode(CalculationDetails.self, from: data)
        }
    }
}

