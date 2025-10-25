import Testing
import Foundation
@testable import Aether

@Suite("Question Model Tests")
struct QuestionModelTests {
    @Test("Decode multiple choice question")
    func decodeMultipleChoiceQuestion() throws {
        let json = """
            {
                "question_id": "123e4567-e89b-12d3-a456-426614174000",
                "question_type": "multiple_choice",
                "text": "What is 2 + 2?",
                "details": {
                    "question_type": "multiple_choice",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": 1
                }
            }
            """
        let data = try #require(json.data(using: .utf8))
        let question = try JSONDecoder().decode(AnyQuestion.self, from: data)
        
        #expect(question.text == "What is 2 + 2?")
        #expect(question.questionType == .multipleChoice)
        #expect(question.id.uuidString.lowercased() == "123e4567-e89b-12d3-a456-426614174000")
        
        if case let .multipleChoice(mcQuestion) = question {
            #expect(mcQuestion.details.options == ["3", "4", "5", "6"])
            #expect(mcQuestion.details.correctAnswer == 1)
        } else {
            Issue.record("Expected multiple choice question")
        }
    }
    
    
    @Test("Decode fill in the blank question")
        func decodeFillInTheBlankQuestion() throws {
            let json = """
            {
                "question_id": "223e4567-e89b-12d3-a456-426614174001",
                "question_type": "fill_in_the_blank",
                "text": "The capital of France is ___.",
                "details": {
                    "question_type": "fill_in_the_blank",
                    "expected_answer": ["Paris", "paris"]
                }
            }
            """
            
            let data = try #require(json.data(using: .utf8))
            let question = try JSONDecoder().decode(AnyQuestion.self, from: data)
            
            #expect(question.text == "The capital of France is ___.")
            #expect(question.questionType == .fillInTheBlank)
            
            guard case .fillInTheBlank(let fibQuestion) = question else {
                Issue.record("Expected fill in the blank question")
                return
            }
            
            #expect(fibQuestion.details.expectedAnswer == ["Paris", "paris"])
        }

        
        // MARK: - Calculation Tests
        
        @Test("Decode calculation question")
        func decodeCalculationQuestion() throws {
            let json = """
            {
                "question_id": "323e4567-e89b-12d3-a456-426614174002",
                "question_type": "calculation",
                "text": "What is π to 2 decimal places?",
                "details": {
                    "expected_answer": ["3.14", "3.141"],
                    "precision": 2
                }
            }
            """
            let data = try #require(json.data(using: .utf8))
            let question = try JSONDecoder().decode(AnyQuestion.self, from: data)
            
            #expect(question.text == "What is π to 2 decimal places?")
            #expect(question.questionType == .calculation)
            
            guard case .calculation(let calcQuestion) = question else {
                Issue.record("Expected calculation question")
                return
            }
            
            #expect(calcQuestion.details.expectedAnswer == ["3.14", "3.141"])
            #expect(calcQuestion.details.precision == 2)
        }
}


