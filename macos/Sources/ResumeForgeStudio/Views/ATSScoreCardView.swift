import SwiftUI

public struct ATSScoreCardView: View {
    public let app: Application
    @ObservedObject private var dataManager = DataManager.shared
    @State private var showingJDSheet = false

    public init(app: Application) {
        self.app = app
    }

    private var matchScore: Int {
        dataManager.currentATSResult?.match_rate_percent ?? 50
    }

    private var scoreGrade: String {
        if matchScore >= 85 { return "A+ High Match" }
        if matchScore >= 70 { return "A Solid Match" }
        if matchScore >= 50 { return "B Average" }
        return "C Needs Tuning"
    }

    private var scoreColor: Color {
        if matchScore >= 75 { return .green }
        if matchScore >= 50 { return .orange }
        return .red
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header Row: Gauge + ATS Badge + Actions
            HStack(spacing: 12) {
                // Circular Match Score Gauge
                ZStack {
                    Circle()
                        .stroke(Color.secondary.opacity(0.2), lineWidth: 5)
                        .frame(width: 46, height: 46)

                    Circle()
                        .trim(from: 0, to: CGFloat(matchScore) / 100.0)
                        .stroke(scoreColor, style: StrokeStyle(lineWidth: 5, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        .frame(width: 46, height: 46)

                    Text("\(matchScore)%")
                        .font(.system(size: 13, weight: .bold, design: .rounded))
                        .foregroundStyle(scoreColor)
                }

                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 6) {
                        Text("ATS Match Radar")
                            .font(.subheadline)
                            .fontWeight(.bold)

                        Text(scoreGrade)
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 1.5)
                            .background(scoreColor.opacity(0.15))
                            .foregroundStyle(scoreColor)
                            .cornerRadius(4)

                        if let timeMs = dataManager.currentATSResult?.compilation_time_ms {
                            Text("⚡ \(Double(timeMs) / 1000.0, specifier: "%.1f")s")
                                .font(.caption2)
                                .fontWeight(.semibold)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1.5)
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

                // Action Cluster
                HStack(spacing: 8) {
                    // 1. One-Click ATS Boost Button
                    Button(action: {
                        Task {
                            await dataManager.autoTailor(for: app)
                        }
                    }) {
                        HStack(spacing: 5) {
                            if dataManager.isTailoring {
                                ProgressView()
                                    .controlSize(.small)
                                Text("Boosting...")
                            } else {
                                Image(systemName: "sparkles")
                                    .foregroundStyle(.yellow)
                                Text("⚡ One-Click ATS Boost")
                                    .fontWeight(.semibold)
                            }
                        }
                        .padding(.horizontal, 9)
                        .padding(.vertical, 5)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.purple)
                    .disabled(dataManager.isTailoring)
                    .help("Injects missing technical skills & best GitHub projects to boost score in < 2s")

                    // 2. Custom JD & Presets Button
                    Button(action: { showingJDSheet = true }) {
                        HStack(spacing: 4) {
                            Image(systemName: "doc.text.magnifyingglass")
                            Text("JD & Presets")
                        }
                        .font(.caption)
                    }
                    .buttonStyle(.bordered)
                    .help("Paste real job description from recruiter or pick a domain preset")

                    // 3. GitHub Re-scan Button
                    Button(action: {
                        Task {
                            await dataManager.triggerGitHubScan()
                        }
                    }) {
                        Image(systemName: "arrow.triangle.2.circlepath")
                            .font(.caption)
                    }
                    .buttonStyle(.bordered)
                    .help("Re-scan GitHub for newly pushed repos & commits")
                }
            }

            // Keyword Alignment Section
            VStack(alignment: .leading, spacing: 6) {
                // Matched Keywords (Read-only pills)
                if let matched = dataManager.currentATSResult?.matched_keywords, !matched.isEmpty {
                    HStack(alignment: .top, spacing: 6) {
                        Text("Matched:")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .frame(width: 54, alignment: .leading)

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

                // Missing Keywords (INTERACTIVE CLICKABLE INJECTION PILLS)
                if let missing = dataManager.currentATSResult?.missing_keywords, !missing.isEmpty {
                    HStack(alignment: .top, spacing: 6) {
                        Text("Missing:")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .frame(width: 54, alignment: .leading)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 5) {
                                ForEach(missing, id: \.self) { kw in
                                    Button(action: {
                                        Task {
                                            await dataManager.injectKeyword(app: app, keyword: kw)
                                        }
                                    }) {
                                        HStack(spacing: 3) {
                                            Image(systemName: "plus.circle.fill")
                                                .font(.system(size: 9))
                                            Text(kw)
                                                .font(.system(size: 10, weight: .medium))
                                        }
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2.5)
                                        .background(Color.orange.opacity(0.15))
                                        .foregroundStyle(.orange)
                                        .cornerRadius(4)
                                    }
                                    .buttonStyle(.plain)
                                    .help("Click to inject '\(kw)' into resume and immediately boost ATS match score")
                                }
                            }
                        }
                    }
                }

                // Synced Tailored Projects Badge
                if let projs = dataManager.currentATSResult?.tailored_projects, !projs.isEmpty {
                    HStack(spacing: 6) {
                        Text("Tailored Repos:")
                            .font(.caption2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)
                            .frame(width: 54, alignment: .leading)

                        ForEach(projs, id: \.self) { p in
                            Text(p)
                                .font(.system(size: 10, weight: .semibold))
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1.5)
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
        .sheet(isPresented: $showingJDSheet) {
            CustomJDSheet(application: app, isPresented: $showingJDSheet)
        }
    }
}
