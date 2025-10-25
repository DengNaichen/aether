import SwiftUI
import SpriteKit

// A SwiftUI view that shows a confetti animation.
struct ConfettiView: View {
    @State private var animate = false
    @State private var confettiPieces: [ConfettiPiece] = []
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // SwiftUI-based confetti for better Preview support
                ForEach(confettiPieces) { piece in
                    Rectangle()
                        .fill(piece.color)
                        .frame(width: piece.size.width, height: piece.size.height)
                        .rotationEffect(.degrees(piece.rotation))
                        .position(piece.position)
                        .opacity(piece.opacity)
                }
            }
            .onAppear {
                createConfettiPieces(in: geometry.size)
                startAnimation()
            }
        }
        .allowsHitTesting(false) // Allow touches to pass through
    }
    
    private func createConfettiPieces(in size: CGSize) {
        let colors: [Color] = [.red, .blue, .green, .yellow, .orange, .purple, .cyan, .pink]
        
        confettiPieces = (0..<100).map { _ in
            ConfettiPiece(
                id: UUID(),
                position: CGPoint(
                    x: CGFloat.random(in: 0...size.width),
                    y: -50
                ),
                size: CGSize(
                    width: CGFloat.random(in: 6...12),
                    height: CGFloat.random(in: 6...12)
                ),
                color: colors.randomElement() ?? .blue,
                rotation: Double.random(in: 0...360),
                fallSpeed: Double.random(in: 3...8),
                horizontalDrift: Double.random(in: -100...100),
                opacity: Double.random(in: 0.7...1.0)
            )
        }
    }
    
    private func startAnimation() {
        guard let screenSize = UIScreen.main.bounds.size as CGSize? else { return }
        
        for i in confettiPieces.indices {
            let piece = confettiPieces[i]
            let delay = Double.random(in: 0...2.0)
            
            DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
                withAnimation(
                    .linear(duration: piece.fallSpeed)
                    .repeatCount(1, autoreverses: false)
                ) {
                    confettiPieces[i].position = CGPoint(
                        x: piece.position.x + piece.horizontalDrift,
                        y: screenSize.height + 100
                    )
                    confettiPieces[i].rotation += 720 // Two full rotations
                }
                
                // Fade out effect
                DispatchQueue.main.asyncAfter(deadline: .now() + piece.fallSpeed * 0.7) {
                    withAnimation(.easeOut(duration: piece.fallSpeed * 0.3)) {
                        confettiPieces[i].opacity = 0
                    }
                }
            }
        }
    }
}

// MARK: - Confetti Piece Model
struct ConfettiPiece: Identifiable {
    let id: UUID
    var position: CGPoint
    let size: CGSize
    let color: Color
    var rotation: Double
    let fallSpeed: Double
    let horizontalDrift: Double
    var opacity: Double
}

// MARK: - SpriteKit Fallback (for production use)
struct SpriteKitConfettiView: UIViewRepresentable {
    func makeUIView(context: Context) -> SKView {
        let skView = SKView()
        skView.backgroundColor = .clear
        let scene = SKScene(size: skView.bounds.size)
        scene.backgroundColor = .clear
        
        // Safely load the confetti emitter file
        if let emitter = SKEmitterNode(fileNamed: "Confetti.sks") {
            emitter.position = CGPoint(x: scene.size.width / 2, y: scene.size.height)
            emitter.particlePositionRange = CGVector(dx: scene.size.width, dy: 0)
            scene.addChild(emitter)
        } else {
            // Fallback: Create a simple programmatic confetti effect
            createProgrammaticConfetti(in: scene)
        }
        
        skView.presentScene(scene)
        
        return skView
    }
    
    func updateUIView(_ uiView: SKView, context: Context) {
        uiView.scene?.size = uiView.bounds.size
    }
    
    // MARK: - Fallback Confetti Implementation
    private func createProgrammaticConfetti(in scene: SKScene) {
        let colors: [UIColor] = [.red, .blue, .green, .yellow, .orange, .purple, .cyan]
        
        for i in 0..<50 {
            let confettiPiece = SKShapeNode(rectOf: CGSize(width: 10, height: 10))
            confettiPiece.fillColor = colors.randomElement() ?? .blue
            confettiPiece.position = CGPoint(
                x: CGFloat.random(in: 0...scene.size.width),
                y: scene.size.height + 50
            )
            
            // Add rotation
            let rotateAction = SKAction.rotate(byAngle: .pi * 2, duration: Double.random(in: 1...3))
            let repeatRotation = SKAction.repeatForever(rotateAction)
            
            // Add falling movement
            let fallAction = SKAction.moveBy(
                x: CGFloat.random(in: -100...100),
                y: -scene.size.height - 100,
                duration: Double.random(in: 3...6)
            )
            
            // Combine actions
            let group = SKAction.group([repeatRotation, fallAction])
            
            // Remove after animation
            let removeAction = SKAction.removeFromParent()
            let sequence = SKAction.sequence([group, removeAction])
            
            confettiPiece.run(sequence)
            scene.addChild(confettiPiece)
        }
    }
}