import SwiftUI

public struct ATSInspectorView: View {
    public let app: Application
    @ObservedObject private var dataManager = DataManager.shared
    @State private var showingJDSheet = false
    @State private var showingDiffSheet = false

    public init(app: Application) {
        self.app = app
    }

    private var atsResult: ATSResult? {
        dataManager.currentATSResult
    }

    private var matchScore: Int {
        atsResult?.match_rate_percent ?? 50
    }

    private var scoreGrade: String {
        if matchScore >= 85 { return "A+ Match" }
        if matchScore >= 70 { return "A Solid" }
        if matchScore >= 50 { return "B Average" }
        return "C Needs Tuning"
    }

    private var scoreColor: Color {
        if matchScore >= 75 { return .green }
        if matchScore >= 50 { return .orange }
        return .red
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                // Error Alert Banner
                if let err = dataManager.errorMessage {
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.red)
                            .padding(.top, 2)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("ATS Pipeline Notice")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundStyle(.red)
                            Text(err)
                                .font(.caption2)
                                .foregroundStyle(.primary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        Spacer()
                        Button(action: { dataManager.errorMessage = nil }) {
                            Image(systemName: "xmark")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(10)
                    .background(Color.red.opacity(0.12))
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.red.opacity(0.3), lineWidth: 1))
                }

                // Daemon Offline Warning
                if !dataManager.daemonOnline {
                    HStack(spacing: 8) {
                        Image(systemName: "bolt.slash.fill")
                            .foregroundStyle(.yellow)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Daemon Offline")
                                .font(.caption)
                                .fontWeight(.bold)
                            Text("Tracker daemon (:5999) disconnected.")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Button("Reconnect") {
                            Task {
                                await dataManager.fetchApplications()
                                await dataManager.fetchATSScore(for: app)
                            }
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                    }
                    .padding(10)
                    .background(Color.yellow.opacity(0.12))
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.yellow.opacity(0.3), lineWidth: 1))
                }

                // Page Budget Overflow Warning
                if let budget = atsResult?.page_budget_percent, budget > 105 {
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "doc.badge.ellipsis")
                            .font(.headline)
                            .foregroundStyle(.orange)
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Page Overflow Warning (\(budget)%)")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundStyle(.orange)
                            Text("Content volume is at \(budget)%. Trim 2-3 bullets to ensure strict 1-page compliance.")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                    .padding(10)
                    .background(Color.orange.opacity(0.12))
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.orange.opacity(0.3), lineWidth: 1))
                }

                // Loading State when no ATS result is available yet
                if dataManager.isATSLoading && atsResult == nil {
                    VStack(spacing: 10) {
                        ProgressView()
                            .controlSize(.regular)
                        Text("Auditing ATS Keywords...")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(24)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(10)
                }

                // 1. Radar Score Header Card
                VStack(spacing: 12) {
                    HStack(spacing: 14) {
                        // Circular Composite Gauge
                        ZStack {
                            Circle()
                                .stroke(Color.secondary.opacity(0.18), lineWidth: 6)
                                .frame(width: 58, height: 58)

                            Circle()
                                .trim(from: 0, to: CGFloat(matchScore) / 100.0)
                                .stroke(scoreColor, style: StrokeStyle(lineWidth: 6, lineCap: .round))
                                .rotationEffect(.degrees(-90))
                                .frame(width: 58, height: 58)

                            VStack(spacing: 0) {
                                Text("\(matchScore)%")
                                    .font(.system(size: 15, weight: .bold, design: .rounded))
                                    .foregroundStyle(scoreColor)
                            }
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            HStack(spacing: 6) {
                                Text("ATS Match Radar")
                                    .font(.headline)
                                    .fontWeight(.bold)

                                Text(scoreGrade)
                                    .font(.caption2)
                                    .fontWeight(.semibold)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 1.5)
                                    .background(scoreColor.opacity(0.15))
                                    .foregroundStyle(scoreColor)
                                    .cornerRadius(4)
                            }

                            HStack(spacing: 6) {
                                if let timeMs = atsResult?.compilation_time_ms {
                                    Text("⚡ \(Double(timeMs) / 1000.0, specifier: "%.1f")s compile")
                                        .font(.caption2)
                                        .fontWeight(.semibold)
                                        .foregroundStyle(.green)
                                }
                                Text("•")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                Text(atsResult?.page_status ?? "Strict 1-Page")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                        }

                        Spacer()
                    }

                    // 2. Primary 1-Click Action Cluster
                    VStack(spacing: 8) {
                        Button(action: {
                            Task { await dataManager.autoTailor(for: app) }
                        }) {
                            HStack(spacing: 6) {
                                if dataManager.isTailoring {
                                    ProgressView().controlSize(.small)
                                    Text("Boosting & Compiling...")
                                } else {
                                    Image(systemName: "sparkles")
                                    Text("⚡ One-Click ATS Boost")
                                        .fontWeight(.semibold)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.purple)
                        .disabled(dataManager.isTailoring)
                        .help("Injects missing technical skills & best GitHub projects in < 2s")

                        HStack(spacing: 8) {
                            Button(action: { showingDiffSheet = true }) {
                                HStack(spacing: 4) {
                                    Image(systemName: "arrow.triangle.swap")
                                    Text("Review Diff")
                                }
                                .font(.caption)
                                .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)
                            .help("Preview tailored bullet changes and score deltas")

                            Button(action: { showingJDSheet = true }) {
                                HStack(spacing: 4) {
                                    Image(systemName: "doc.text.magnifyingglass")
                                    Text("Custom JD")
                                }
                                .font(.caption)
                                .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)
                            .help("Paste target job description or choose domain presets")
                        }
                    }
                }
                .padding(14)
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(10)

                // 3. Four-Pillar Calibrated Breakdown
                VStack(alignment: .leading, spacing: 10) {
                    Text("4-PILLAR CALIBRATION")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundStyle(.secondary)

                    VStack(spacing: 8) {
                        let pillars = atsResult?.pillars
                        PillarProgressRow(
                            title: "Core Tech Match (40%)",
                            value: pillars?.core_tech ?? min(100, matchScore + 5),
                            icon: "cpu"
                        )
                        PillarProgressRow(
                            title: "Domain Vector Fit (30%)",
                            value: pillars?.domain_relevance ?? max(40, matchScore - 5),
                            icon: "chart.line.uptrend.xyaxis"
                        )
                        PillarProgressRow(
                            title: "Google XYZ Metrics (20%)",
                            value: pillars?.impact_metrics ?? 85,
                            icon: "target"
                        )
                        PillarProgressRow(
                            title: "Page Budget (10%)",
                            value: pillars?.page_budget ?? 100,
                            icon: "doc.plaintext"
                        )
                    }
                }
                .padding(12)
                .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
                .cornerRadius(8)

                // 4. Missing Keywords (Interactive 1-Click Injection Chips)
                if let missing = atsResult?.missing_keywords, !missing.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("MISSING COMPETENCIES (\(missing.count))")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .foregroundStyle(.orange)
                            Spacer()
                            Text("Click to inject")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }

                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 95), spacing: 6)], spacing: 6) {
                            ForEach(missing, id: \.self) { kw in
                                Button(action: {
                                    Task { await dataManager.injectKeyword(app: app, keyword: kw) }
                                }) {
                                    HStack(spacing: 3) {
                                        Image(systemName: "plus")
                                            .font(.system(size: 8, weight: .bold))
                                        Text(kw)
                                            .font(.system(size: 10, weight: .medium))
                                            .lineLimit(1)
                                    }
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3.5)
                                    .frame(maxWidth: .infinity)
                                    .background(Color.orange.opacity(0.14))
                                    .foregroundStyle(.orange)
                                    .cornerRadius(5)
                                }
                                .buttonStyle(.plain)
                                .help("Inject '\(kw)' into skills and recompile tailored PDF")
                            }
                        }
                    }
                    .padding(12)
                    .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
                    .cornerRadius(8)
                }

                // 5. Matched Keywords (Read-Only Badges)
                if let matched = atsResult?.matched_keywords, !matched.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("VERIFIED MATCHES (\(matched.count))")
                            .font(.caption2)
                            .fontWeight(.bold)
                            .foregroundStyle(.green)

                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 90), spacing: 6)], spacing: 6) {
                            ForEach(matched, id: \.self) { kw in
                                HStack(spacing: 3) {
                                    Image(systemName: "checkmark")
                                        .font(.system(size: 8, weight: .bold))
                                    Text(kw)
                                        .font(.system(size: 10, weight: .medium))
                                        .lineLimit(1)
                                }
                                .padding(.horizontal, 6)
                                .padding(.vertical, 3)
                                .frame(maxWidth: .infinity)
                                .background(Color.green.opacity(0.12))
                                .foregroundStyle(.green)
                                .cornerRadius(5)
                            }
                        }
                    }
                    .padding(12)
                    .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
                    .cornerRadius(8)
                }

                // 6. Tailored Original Projects
                if let projs = atsResult?.tailored_projects, !projs.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("PERSONAL PROJECTS (ORIGINAL)")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .foregroundStyle(.blue)
                            Spacer()
                            Text("Independent Work")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }

                        ForEach(projs, id: \.self) { p in
                            HStack {
                                Image(systemName: "folder.fill")
                                    .font(.caption2)
                                    .foregroundStyle(.blue)
                                Text(p)
                                    .font(.caption)
                                    .fontWeight(.medium)
                                Spacer()
                                Text("Author")
                                    .font(.system(size: 9, weight: .semibold))
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 1.5)
                                    .background(Color.blue.opacity(0.12))
                                    .foregroundStyle(.blue)
                                    .cornerRadius(3)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.08))
                            .cornerRadius(5)
                        }
                    }
                    .padding(12)
                    .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
                    .cornerRadius(8)
                }

                // 7. Open-Source Upstream Contributions (Forks)
                if let foss = atsResult?.tailored_open_source, !foss.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("OPEN-SOURCE CONTRIBUTIONS (UPSTREAM FORKS)")
                                .font(.caption2)
                                .fontWeight(.bold)
                                .foregroundStyle(.purple)
                            Spacer()
                            Text("Upstream PRs / Patches")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }

                        ForEach(foss, id: \.self) { item in
                            HStack {
                                Image(systemName: "arrow.triangle.branch")
                                    .font(.caption2)
                                    .foregroundStyle(.purple)
                                Text(item)
                                    .font(.caption)
                                    .fontWeight(.medium)
                                Spacer()
                                Text("Contributor")
                                    .font(.system(size: 9, weight: .semibold))
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 1.5)
                                    .background(Color.purple.opacity(0.12))
                                    .foregroundStyle(.purple)
                                    .cornerRadius(3)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.purple.opacity(0.08))
                            .cornerRadius(5)
                        }
                    }
                    .padding(12)
                    .background(Color(NSColor.controlBackgroundColor).opacity(0.6))
                    .cornerRadius(8)
                }

                // 7. Actionable Recommendations
                if let suggestions = atsResult?.suggestions, !suggestions.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("RECOMMENDATIONS")
                            .font(.caption2)
                            .fontWeight(.bold)
                            .foregroundStyle(.secondary)

                        ForEach(suggestions, id: \.self) { sug in
                            HStack(alignment: .top, spacing: 6) {
                                Image(systemName: "lightbulb.fill")
                                    .font(.system(size: 9))
                                    .foregroundStyle(.yellow)
                                    .padding(.top, 2)
                                Text(sug)
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .padding(12)
                    .background(Color(NSColor.controlBackgroundColor).opacity(0.4))
                    .cornerRadius(8)
                }
            }
            .padding(14)
        }
        .frame(minWidth: 280, idealWidth: 320, maxWidth: 380)
        .background(Color(NSColor.windowBackgroundColor))
        .sheet(isPresented: $showingJDSheet) {
            CustomJDSheet(application: app, isPresented: $showingJDSheet)
        }
        .sheet(isPresented: $showingDiffSheet) {
            ResumeDiffSheet(application: app, isPresented: $showingDiffSheet)
        }
    }
}

// Mini progress row for the 4-pillar breakdown
private struct PillarProgressRow: View {
    let title: String
    let value: Int
    let icon: String

    private var barColor: Color {
        if value >= 80 { return .green }
        if value >= 60 { return .blue }
        if value >= 40 { return .orange }
        return .red
    }

    var body: some View {
        VStack(spacing: 3) {
            HStack {
                Label(title, systemImage: icon)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundStyle(.primary)
                Spacer()
                Text("\(value)%")
                    .font(.system(size: 10, weight: .bold, design: .rounded))
                    .foregroundStyle(barColor)
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.secondary.opacity(0.15))
                        .frame(height: 5)

                    RoundedRectangle(cornerRadius: 3)
                        .fill(barColor)
                        .frame(width: geo.size.width * CGFloat(min(100, max(0, value))) / 100.0, height: 5)
                }
            }
            .frame(height: 5)
        }
    }
}
