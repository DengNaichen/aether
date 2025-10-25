import Foundation

protocol NetworkViewModeling: ObservableObject {
    var isLoading: Bool { get set }
    var alertItem: AlertItem? { get set }
}

@MainActor
extension NetworkViewModeling {
    
    private func handleError(_ error: Error, withTitle title: String) {
        let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            }
        self.alertItem = AlertItem(title: title, message: errorMessage)
    }
    
    func performTask<T>(errorTitle: String, task: () async throws -> T) async -> T? {
        isLoading = true
        defer { isLoading = false }
        alertItem = nil
        do {
            return try await task()
        } catch {
            handleError(error, withTitle: errorTitle)
            return nil
        }
    }
}


