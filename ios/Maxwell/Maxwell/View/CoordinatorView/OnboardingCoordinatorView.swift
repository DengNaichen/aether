import SwiftUI
import Combine

struct OnboardingCoordinatorView: View {
    @StateObject var coordinator: OnboardingCoordinator

    var body: some View {
        coordinator.start()
    }
}
