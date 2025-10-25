import Foundation
import Combine

//class SessionStartViewModel: ObservableObject, NetworkViewModeling {
//    
//    private let network: NetworkServicing
//    
//    @Published var isLoading: Bool = false
//    @Published var alertItem: AlertItem?
//    
//    @Published var quizProblems: [QuizProblem] = []
//    
//    
//    init(network: NetworkServicing) {
//        self.network = network
//    }
//    
//    func startSession(courseId: String, questionCount: Int) async {
//
//        self.quizProblems = []
//        
//        let response = await performTask(errorTitle: "Session Start Failed") {
//            let requestData = SessionStartRequest(courseId: courseId)
//            let endpoint = QuizEndpoint(startSessionRequest: requestData)
//            return try await self.network.request(
//                endpoint: endpoint, responseType: SessionStartResponse.self)
//        }
//        if let response {
//            self.quizProblems = self.mapToModels(from: response.questions)
//        }
//        
//        
//    }
//    
//    private func mapToModels(from apiQuestions: [AnyQuestion]) -> [QuizProblem] {
//        var uiProblems: [QuizProblem] = []
//        
//        for apiQuestion in apiQuestions {
//            switch apiQuestion {
//            case .multipleChoice(let apiMCQ):
//                let problem = QuizProblem(
//                    id: apiMCQ.id,
//                    text: apiMCQ.text,
//                    options: apiMCQ.details.options,
//                    correctAnswerIndex: apiMCQ.details.correctAnswer
//                )
//                uiProblems.append(problem)
//            case .fillInTheBlank(let apiFITB):
//                print("Ingoring question type: fillInTheBlank, ID: \(apiFITB.id)")
//                continue
//            }
//        }
//        return uiProblems
//    }
//}
