import SwiftUI

private struct ConfettiPiece: Identifiable {
    let id = UUID()
    let color: Color
    let shape: Int
    let scale: CGFloat
    let launchAngle: Double
    let launchSpeed: CGFloat
    let spin: Double
    let wobbleSpeed: Double
    let wobbleAmount: CGFloat
}

struct ConfettiView: View {
    @Binding var isActive: Bool
    @State private var pieces: [ConfettiPiece] = []
    @State private var startDate: Date?

    private let colors: [Color] = [.red, .orange, .yellow, .green, .blue, .purple, .pink, .mint]
    private let gravity: CGFloat = 400
    private let duration: Double = 3.5

    var body: some View {
        GeometryReader { geo in
            if let startDate, !pieces.isEmpty {
                TimelineView(.animation) { timeline in
                    let elapsed = timeline.date.timeIntervalSince(startDate)
                    let cx = geo.size.width / 2
                    let cy = geo.size.height * 0.45
                    Canvas { context, _ in
                        for piece in pieces {
                            let t = CGFloat(elapsed)
                            let vx = piece.launchSpeed * CGFloat(cos(piece.launchAngle))
                            let vy = piece.launchSpeed * CGFloat(sin(piece.launchAngle))
                            let x = cx + vx * t + piece.wobbleAmount * CGFloat(sin(piece.wobbleSpeed * elapsed))
                            let y = cy + vy * t + 0.5 * gravity * t * t
                            let angle = Angle.degrees(piece.spin * elapsed)
                            let opacity = max(0, 1.0 - elapsed / duration)

                            context.opacity = opacity
                            context.translateBy(x: x, y: y)
                            context.rotate(by: angle)

                            let s = 8 * piece.scale
                            let rect = CGRect(x: -s / 2, y: -s / 2, width: s, height: s)
                            switch piece.shape {
                            case 0:
                                context.fill(Circle().path(in: rect), with: .color(piece.color))
                            case 1:
                                let r = CGRect(x: -s * 0.4, y: -s / 2, width: s * 0.8, height: s)
                                context.fill(Rectangle().path(in: r), with: .color(piece.color))
                            default:
                                var tri = Path()
                                tri.move(to: CGPoint(x: 0, y: -s / 2))
                                tri.addLine(to: CGPoint(x: s / 2, y: s / 2))
                                tri.addLine(to: CGPoint(x: -s / 2, y: s / 2))
                                tri.closeSubpath()
                                context.fill(tri, with: .color(piece.color))
                            }

                            context.rotate(by: -angle)
                            context.translateBy(x: -x, y: -y)
                        }
                    }
                }
            }
        }
        .allowsHitTesting(false)
        .onChange(of: isActive) { _, active in
            if active { startConfetti() }
        }
    }

    private func startConfetti() {
        pieces = (0..<80).map { _ in
            ConfettiPiece(
                color: colors.randomElement()!,
                shape: Int.random(in: 0...2),
                scale: CGFloat.random(in: 0.6...1.4),
                launchAngle: Double.random(in: -Double.pi * 0.85 ... -Double.pi * 0.15),
                launchSpeed: CGFloat.random(in: 250...550),
                spin: Double.random(in: 200...600) * (Bool.random() ? 1 : -1),
                wobbleSpeed: Double.random(in: 2...6),
                wobbleAmount: CGFloat.random(in: 10...30)
            )
        }
        startDate = .now

        DispatchQueue.main.asyncAfter(deadline: .now() + duration) {
            pieces = []
            startDate = nil
            isActive = false
        }
    }
}
