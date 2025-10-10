//
//  Answer.swift
//  Maxwell
//
//  Created by Daniel on 2025-09-30.
//


import SwiftUI
import Combine


//class QuizViewModel: ObservableObject {
//    // MARK: - Published Properties (for the View)
//    // the full list of questions for the quiz
//    @Published var questions: [MultipleChoiceQuestion] = []
//    
//    // the index of the question currenty being displaced
//    @Published var currentQuestionIndex = 0
//    
//    // State for the current question
//    @Published var selectedOptionIndex: Int?
//    @Published var isAnswerSubmitted = false
//    
//    // Overall quiz state
//    @Published var score = 0
//    
//    // MARK: - Private Properties
//    private var questionLoader = QuestionLoader()
//    
//    
//    // MARK: - Computed Properties
//    // Provide the access to the current quesiton object
//    var currentQuestion: MultipleChoiceQuestion? {
//        guard questions.indices.contains(currentQuestionIndex) else {
//            return nil
//        }
//        return questions[currentQuestionIndex]
//    }
//    
//    // A flag to check if the quiz is over
//    var isQuizFinished: Bool {
//        return currentQuestionIndex >= questions.count
//    }
//    
//    // MARK: - Initialization
//    init() {
//        loadQuiz()
//    }
//    
//    func loadQuiz() {
//        self.questions = questionLoader.LoadQuestions(from: "testProblems")
//    }
//    
//    func submitAnswer() {
//        guard let selectedIndex = selectedOptionIndex, let question = currentQuestion else {
//            return
//        }
//        if selectedOptionIndex == question.correctAnswerIndex {
//            score += 1
//        }
//        isAnswerSubmitted = true
//    }
//    func nextQuestion() {
//        // Make suer we are not at the end
//        if currentQuestionIndex < questions.count - 1 {
//            currentQuestionIndex += 1
//            resetForNextQuestion()
//        } else {
//            currentQuestionIndex += 1
//        }
//    }
//    private func resetForNextQuestion() {
//        selectedOptionIndex = nil
//        isAnswerSubmitted = false
//    }
//    
//    func restartQuiz() {
//        score = 0
//        currentQuestionIndex = 0
//        resetForNextQuestion()
//    }
//}

