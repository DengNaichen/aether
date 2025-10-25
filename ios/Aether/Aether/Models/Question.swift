import Foundation

enum QuestionType: String, Codable {
    case multipleChoice = "multiple_choice"
    case fillInTheBlank = "fill_in_the_blank"
    case calculation = "calculation"
}

protocol QuestionDetails: Codable, Equatable {}

struct MultipleChoiceDetails: QuestionDetails {
    let options: [String]
    let correctAnswer: Int
    
    enum CodingKeys: String, CodingKey {
        case options
        case correctAnswer = "correct_answer"
    }
}

struct FillInTheBlankDetails: QuestionDetails {
    // TODO: this is same as backend, but we wont use it for this version
    let expectedAnswer: [String]
    enum CodingKeys: String, CodingKey {
        case expectedAnswer = "expected_answer"
    }
}

struct CalculationDetails: QuestionDetails {
    // TODO: this is same as backend, but we wont use it for this version
    let expectedAnswer: [String]
    let precision: Int
    
    enum CodingKeys: String, CodingKey {
        
        case precision
        case expectedAnswer = "expected_answer"
    }
}

struct Question<Details: QuestionDetails>: Codable, Equatable {
    let id: UUID
    let text: String
    let details: Details
    
    enum CodingKeys: String, CodingKey {
        case text, details
        case id = "question_id"
    }
}

typealias MultipleChoiceQuestion = Question<MultipleChoiceDetails>
typealias FillInTheBlankQuestion = Question<FillInTheBlankDetails>
typealias CalculationQuestion = Question<CalculationDetails>


enum AnyQuestion: Codable, Equatable {
    case multipleChoice(MultipleChoiceQuestion)
    case fillInTheBlank(FillInTheBlankQuestion)
    case calculation(CalculationQuestion)
    
    private enum CodingKeys: String, CodingKey {
        case questionType = "question_type"
    }
    
    init(from decode: Decoder) throws {
        let container = try decode.container(keyedBy: CodingKeys.self)
        let type = try container.decode(QuestionType.self, forKey: .questionType)
        
        switch type {
        case .multipleChoice:
            let question = try MultipleChoiceQuestion(from: decode)
            self = .multipleChoice(question)
        case .fillInTheBlank:
            let question = try FillInTheBlankQuestion(from: decode)
            self = .fillInTheBlank(question)
        case .calculation:
            let question = try CalculationQuestion(from: decode)
            self = .calculation(question)
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        switch self {
        case .multipleChoice(let question):
            try container.encode(QuestionType.multipleChoice, forKey: .questionType)
            try question.encode(to: encoder)
        case .fillInTheBlank(let question):
            try container.encode(QuestionType.fillInTheBlank, forKey: .questionType)
            try question.encode(to: encoder)
        case .calculation(let question):
            try container.encode(QuestionType.calculation, forKey: .questionType)
        }
    }

    var id: UUID {
        switch self {
        case .multipleChoice(let q): return q.id
        case .fillInTheBlank(let q): return q.id
        case .calculation(let q): return q.id
        }
    }

    var text: String {
        switch self {
        case .multipleChoice(let q): return q.text
        case .fillInTheBlank(let q): return q.text
        case .calculation(let q): return q.text
        }
    }
    
    var questionType: QuestionType {
        switch self {
        case .multipleChoice: return .multipleChoice
        case .fillInTheBlank: return .fillInTheBlank
        case .calculation: return .calculation
        }
    }
}
