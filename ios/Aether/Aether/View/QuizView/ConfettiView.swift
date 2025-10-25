import SwiftUI
import SpriteKit

// A SwiftUI view that shows a confetti animation.
struct ConfettiView: UIViewRepresentable {
    func makeUIView(context: Context) -> SKView {
        let skView = SKView()
        skView.backgroundColor = .clear
        let scene = SKScene(size: skView.bounds.size)
        scene.backgroundColor = .clear
        
        let emitter = SKEmitterNode(fileNamed: "Confetti.sks")!
        emitter.position = CGPoint(x: scene.size.width / 2, y: scene.size.height)
        emitter.particlePositionRange = CGVector(dx: scene.size.width, dy: 0)
        
        scene.addChild(emitter)
        skView.presentScene(scene)
        
        return skView
    }
    
    func updateUIView(_ uiView: SKView, context: Context) {
        uiView.scene?.size = uiView.bounds.size
    }
}