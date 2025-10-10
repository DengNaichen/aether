import Foundation
import Combine

// 假设 AlertItem 和 NetworkServicing 已经定义

class SessionStartViewModel: ObservableObject {
    
    private let network: NetworkServicing
    
    @Published var isLoading: Bool = false
//    @Published var sessionResponse: SessionStartResponse? = nil // 对应 SessionStartResponse 模型
    @Published var alertItem: AlertItem?
    
    @Published var quizProblems: [QuizProblem] = []
    
    
    init(network: NetworkServicing) {
        self.network = network
    }
    
    /// 根据课程ID和问题数量，开始一个新的学习会话
    func startSession(courseId: String, questionCount: Int) async {
        // 1. 设置初始状态
        isLoading = true
        defer { isLoading = false } // 确保函数退出时，加载状态恢复为 false
        alertItem = nil
        self.quizProblems = []
        
        do {
            // 2. 准备并发送网络请求
            let requestData = SessionStartRequest(courseId: courseId)
            let sessionEndpoint = SessionStartEndpoint(startSessionRequest: requestData)
            
            let response: SessionStartResponse = try await network.request(
                endpoint: sessionEndpoint,
                responseType: SessionStartResponse.self
            )
            
            let mappedProblems = self.mapToModels(from: response.questions)
            await MainActor.run {
                self.quizProblems = mappedProblems
            }
            
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "An unknown error happen: \(error.localizedDescription)"
            }
            
            await MainActor.run {
                alertItem = AlertItem(title: "Session Start Failed",
                                      message: errorMessage)
            }
        }
        
        
    }
    
    private func mapToModels(from apiQuestions: [AnyQuestion]) -> [QuizProblem] {
        var uiProblems: [QuizProblem] = []
        
        for apiQuestion in apiQuestions {
            switch apiQuestion {
            case .multipleChoice(let apiMCQ):
                let problem = QuizProblem(
                    id: apiMCQ.id,
                    text: apiMCQ.text,
                    options: apiMCQ.details.options,
                    correctAnswerIndex: apiMCQ.details.correctAnswer
                )
                uiProblems.append(problem)
            case .fillInTheBlank(let apiFITB):
                print("Ingoring question type: fillInTheBlank, ID: \(apiFITB.id)")
                continue
            }
        }
        return uiProblems
    }
}
