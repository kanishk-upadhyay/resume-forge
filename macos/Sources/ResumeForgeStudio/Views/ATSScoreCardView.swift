import SwiftUI

public struct ATSScoreCardView: View {
    public let app: Application
    @ObservedObject private var dataManager = DataManager.shared

    public init(app: Application) {
        self.app = app
    }

    private var matchScore: Int {
        dataManager.currentATSResult?.match_rate_percent ?? 50
    }

    private var scoreColor: Color {
        if matchScore >= 75 { return .green }
        if matchScore >= 50 { return .orange }
        return .red
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header: Circular Match Score + Single Page Badge
            HStack(spacing: 14) {
                // Circular Gauge
                ZStack {
                    Circle()
                        .stroke(Color.secondary.opacity(0.2), lineWidth: 5)
                        .frame(width: 48, height: 48)

                    Circle()
                        .trim(from: 0, to: CGFloat(matchScore) / 100.0)
                        .stroke(scoreColor, style: StrokeStyle(lineWidth: 5, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        .frame(width: 48, height: 48)

                    Text("\(matchScore)%")
                        .font(.system(size: 13, weight: .bold, design: .rounded))
                        .foregroundStyle(scoreColor)
                }

                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 6) {
                        Text("ATS Match Radar")
                            .font(.subheadline)
                            .fontWeight(.bold)
                        
                        if let timeMs = dataManager.currentATSResult?.compilation_time_ms {
                            Text("⚡ \(Double(timeMs) / 1000.0, specifier: "%.1f")s")
                                .font(.caption2)
                                .fontWeight(.semibold)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background(Color.green.opacity(0.15))
                                .foregroundStyle(.green)
                                .cornerRadius(4)
                        }
                    }

                    HStack(spacing: 6) {
                        Image(systemName: "checkmark.seal.fill")
                            .font(.caption2)
                            .foregroundStyle(.blue)
                        Text(dataManager.currentATSResult?.page_status ?? "Strict Single Page (100% Budget)")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer()

                // [✨ Auto-Tailor Bullets] Button
                Button(action: {
                    Task {
                        await dataManager.autoTailor(for: app)
                    }
                }) {
                    HStack(spacing: 6) {
                        if dataManager.isTailoring {
                            ProgressView()
                                .controlSize(.small)
                            Text("Tailoring...")
                        } else {
                            Image(systemName: "sparkles")
                                .foregroundStyle(.yellow)
                            Text("✨ Auto-Tailor Bullets")
                                .fontWeight(.semibold)
                        }
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent)
                .tint(.purple)
                .disabled(dataManager.isTailoring)

                // Re-scan GitHub Context Button
                Button(action: {
                    Task {
                        await dataManager.triggerGitHubScan()
                    }
                }) {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
                .help("Re-scan GitHub account for newly pushed projects & commits")
            }

            // Keyword Alignment Pills
            VStack(alignment: .leading, spacing: 6) {
                // Matched Keywords
                if let matched = dataManager.currentATSResult?.matched_keywords, !matched.isEmpty {
                    HStack(alignment: .top, spacing: 6) {
                        Text("Matched:")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .frame(width: 52, alignment: .leading)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 5) {
                                ForEach(matched, id: \.self) { kw in
                                    HStack(spacing: 3) {
                                        Image(systemName: "checkmark")
                                            .font(.system(size: 8, weight: .bold))
                                        Text(kw)
                                            .font(.system(size: 10, weight: .medium))
                                    }
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.green.opacity(0.15))
                                    .foregroundStyle(.green)
                                    .cornerRadius(4)
                                }
                            }
                        }
                    }
                }

                // Missing Keywords
                if let missing = dataManager.currentATSResult?.missing_keywords, !missing.isEmpty {
                    HStack(alignment: .top, spacing: 6) {
                        Text("Missing:")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .frame(width: 52, alignment: .leading)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 5) {
                                ForEach(missing, id: \.self) { kw in
                                    HStack(spacing: 3) {
                                        Image(systemName: "plus")
                                            .font(.system(size: 8))
                                        Text(kw)
                                            .font(.system(size: 10, weight: .medium))
                                    }
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Color.orange.opacity(0.12))
                                    .foregroundStyle(.orange)
                                    .cornerRadius(4)
                                }
                            }
                        }
                    }
                }

                // Synced Tailored Projects Badge
                if let projs = dataManager.currentATSResult?.tailored_projects, !projs.isEmpty {
                    HStack(spacing: 6) {
                        Text("Active Projects:")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)

                        ForEach(projs, id: \.self) { p in
                            Text(p)
                                .font(.system(size: 10, weight: .semibold))
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background(Color.blue.opacity(0.12))
                                .foregroundStyle(.blue)
                                .cornerRadius(3)
                        }
                    }
                }
            }
        }
        .padding(12)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.secondary.opacity(0.15), lineWidth: 1)
        )
    }
}
