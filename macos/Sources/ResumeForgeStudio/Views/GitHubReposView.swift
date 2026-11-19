import SwiftUI
import AppKit

// MARK: - Column 2: Repositories List
public struct GitHubRepoListView: View {
    @ObservedObject private var dataManager = DataManager.shared
    @State private var searchFilter: String = ""
    @State private var selectedCategory: String = "ALL"

    public init() {}

    private var filteredRepos: [GitHubRepo] {
        var list = dataManager.githubRepos

        if selectedCategory != "ALL" {
            list = list.filter { repo in
                let cat = (repo.category ?? "").lowercased()
                let name = repo.repo.lowercased()
                switch selectedCategory {
                case "ORIGINALS":
                    return !repo.isFork
                case "FORKS":
                    return repo.isFork
                case "SYSTEMS":
                    return cat.contains("system") || cat.contains("driver") || name.contains("tether") || name.contains("soc") || name.contains("core")
                case "APPS":
                    return cat.contains("app") || cat.contains("fullstack") || cat.contains("web") || name.contains("smartspend") || name.contains("resume")
                default:
                    return true
                }
            }
        }

        if !searchFilter.isEmpty {
            let q = searchFilter.lowercased()
            list = list.filter { repo in
                repo.repo.lowercased().contains(q) ||
                (repo.primary_language?.lowercased().contains(q) ?? false) ||
                (repo.category?.lowercased().contains(q) ?? false) ||
                (repo.ats_bullets?.contains(where: { $0.lowercased().contains(q) }) ?? false)
            }
        }

        return list
    }

    public var body: some View {
        VStack(spacing: 0) {
            // Header Bar & Search
            VStack(spacing: 8) {
                HStack {
                    HStack(spacing: 6) {
                        Image(systemName: "curlybraces.square.fill")
                            .foregroundStyle(.purple)
                        Text("GitHub Context Repos")
                            .font(.headline)
                            .fontWeight(.bold)
                    }
                    Spacer()
                    Text("\(dataManager.githubRepos.count)")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Capsule().fill(Color.purple.opacity(0.15)))
                        .foregroundStyle(.purple)
                }

                // Search field
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Filter repos, languages...", text: $searchFilter)
                        .textFieldStyle(.plain)
                    if !searchFilter.isEmpty {
                        Button(action: { searchFilter = "" }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 5)
                .background(Color(NSColor.controlBackgroundColor))
                .cornerRadius(6)

                // Category filter chips
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 5) {
                        RepoCategoryPill(title: "All", isSelected: selectedCategory == "ALL") {
                            selectedCategory = "ALL"
                        }
                        RepoCategoryPill(title: "Originals", isSelected: selectedCategory == "ORIGINALS") {
                            selectedCategory = "ORIGINALS"
                        }
                        RepoCategoryPill(title: "FOSS Forks", isSelected: selectedCategory == "FORKS") {
                            selectedCategory = "FORKS"
                        }
                        RepoCategoryPill(title: "Systems", isSelected: selectedCategory == "SYSTEMS") {
                            selectedCategory = "SYSTEMS"
                        }
                        RepoCategoryPill(title: "Apps", isSelected: selectedCategory == "APPS") {
                            selectedCategory = "APPS"
                        }
                    }
                }
            }
            .padding(10)
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // Repos list
            if filteredRepos.isEmpty {
                VStack(spacing: 10) {
                    Spacer()
                    Image(systemName: "tray")
                        .font(.system(size: 36))
                        .foregroundStyle(.secondary)
                    Text("No Repositories Found")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
            } else {
                List(filteredRepos, id: \.id, selection: Binding(
                    get: { dataManager.selectedRepo },
                    set: { dataManager.selectedRepo = $0 }
                )) { repo in
                    RepoRowView(repo: repo)
                        .tag(repo)
                        .padding(.vertical, 3)
                }
                .listStyle(.plain)
            }
        }
        .frame(minWidth: 260, idealWidth: 300)
    }
}

// Compact row for the list view
private struct RepoRowView: View {
    let repo: GitHubRepo

    private var repoIcon: String {
        let name = repo.repo.lowercased()
        let cat = (repo.category ?? "").lowercased()
        if name.contains("tether") || cat.contains("driver") || cat.contains("system") {
            return "cpu.fill"
        }
        if cat.contains("foss") || name.contains("gitlab") {
            return "shippingbox.fill"
        }
        return "laptopcomputer"
    }

    private var repoIconColor: Color {
        let name = repo.repo.lowercased()
        if name.contains("tether") { return .blue }
        if name.contains("gitlab") { return .orange }
        return .purple
    }

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: repoIcon)
                .font(.headline)
                .foregroundStyle(repoIconColor)

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text(repo.repo)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .lineLimit(1)

                    Text(repo.repoBadgeTitle)
                        .font(.system(size: 8.5, weight: .semibold))
                        .padding(.horizontal, 4.5)
                        .padding(.vertical, 1.5)
                        .background(repo.isFork ? Color.purple.opacity(0.14) : Color.green.opacity(0.14))
                        .foregroundStyle(repo.isFork ? Color.purple : Color.green)
                        .cornerRadius(3)
                }

                HStack(spacing: 6) {
                    if let lang = repo.primary_language, !lang.isEmpty {
                        Text(lang)
                            .font(.caption2)
                            .foregroundStyle(.blue)
                    }

                    if let bullets = repo.ats_bullets, !bullets.isEmpty {
                        Text("•")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text("\(bullets.count) XYZ bullets")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()

            if let stars = repo.stars, stars > 0 {
                HStack(spacing: 2) {
                    Image(systemName: "star.fill")
                        .font(.system(size: 8))
                        .foregroundStyle(.yellow)
                    Text("\(stars)")
                        .font(.caption2)
                }
                .foregroundStyle(.secondary)
            }
        }
    }
}

private struct RepoCategoryPill: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption2)
                .fontWeight(isSelected ? .bold : .medium)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(isSelected ? Color.purple : Color.secondary.opacity(0.12))
                .foregroundStyle(isSelected ? Color.white : Color.primary)
                .cornerRadius(5)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Column 3: Repository Detail View
public struct GitHubRepoDetailView: View {
    public let repo: GitHubRepo?
    @ObservedObject private var dataManager = DataManager.shared
    @State private var copiedBulletIndex: Int? = nil

    public init(repo: GitHubRepo?) {
        self.repo = repo
    }

    private var repoIcon: String {
        guard let repo = repo else { return "laptopcomputer" }
        let name = repo.repo.lowercased()
        let cat = (repo.category ?? "").lowercased()
        if name.contains("tether") || cat.contains("driver") || cat.contains("system") {
            return "cpu.fill"
        }
        if cat.contains("foss") || name.contains("gitlab") {
            return "shippingbox.fill"
        }
        return "laptopcomputer"
    }

    private var repoIconColor: Color {
        guard let repo = repo else { return .purple }
        let name = repo.repo.lowercased()
        if name.contains("tether") { return .blue }
        if name.contains("gitlab") { return .orange }
        return .purple
    }

    public var body: some View {
        if let repo = repo {
            VStack(spacing: 0) {
                // Header Bar
                HStack(alignment: .center, spacing: 14) {
                    Image(systemName: repoIcon)
                        .font(.system(size: 36))
                        .foregroundStyle(repoIconColor)

                    VStack(alignment: .leading, spacing: 3) {
                        HStack(spacing: 8) {
                            Text(repo.repo)
                                .font(.title2)
                                .fontWeight(.bold)

                            Button(action: { dataManager.openInZen(url: repo.url) }) {
                                HStack(spacing: 4) {
                                    Text("Open on GitHub")
                                    Image(systemName: "arrow.up.right.square")
                                }
                                .font(.caption)
                            }
                            .buttonStyle(.bordered)
                        }

                        HStack(spacing: 8) {
                            if let cat = repo.category, !cat.isEmpty {
                                Text(cat.replacingOccurrences(of: "_", with: " ").capitalized)
                                    .font(.caption)
                                    .fontWeight(.medium)
                                    .foregroundStyle(.secondary)
                            }

                            if let lang = repo.primary_language, !lang.isEmpty {
                                Text("•")
                                    .foregroundStyle(.secondary)
                                Text(lang)
                                    .font(.caption)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(.blue)
                            }

                            if let pushed = repo.last_pushed {
                                Text("•")
                                    .foregroundStyle(.secondary)
                                Text("Last pushed: \(formatDate(pushed))")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }

                    Spacer()

                    // Sync Commits Button
                    Button(action: {
                        Task { await dataManager.triggerGitHubScan() }
                    }) {
                        HStack(spacing: 5) {
                            if dataManager.isSyncingGitHub {
                                ProgressView().controlSize(.small)
                            } else {
                                Image(systemName: "arrow.triangle.2.circlepath")
                            }
                            Text("Sync Commits")
                                .fontWeight(.medium)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.purple)
                    .disabled(dataManager.isSyncingGitHub)
                }
                .padding(16)
                .background(Color(NSColor.windowBackgroundColor))

                Divider()

                // Attribution Banner
                HStack(spacing: 8) {
                    Image(systemName: repo.isFork ? "arrow.triangle.branch" : "sparkles")
                        .font(.caption)
                        .foregroundStyle(repo.isFork ? .purple : .green)
                    Text(repo.isFork ? "Open-Source Upstream Contribution (Fork) — Author of Upstream PRs & Patches" : "Original Personal Project — Authored & Maintained by Kanishk Upadhyay")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(repo.isFork ? .purple : .green)
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 7)
                .background(repo.isFork ? Color.purple.opacity(0.08) : Color.green.opacity(0.08))

                Divider()
                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        // Extracted Google XYZ Bullets Section
                        VStack(alignment: .leading, spacing: 10) {
                            HStack {
                                Label("EXTRACTED GOOGLE XYZ ATS BULLETS", systemImage: "sparkles")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.purple)

                                Spacer()

                                Text("Google XYZ: Accomplished [X] as measured by [Y] by doing [Z]")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }

                            if let bullets = repo.ats_bullets, !bullets.isEmpty {
                                VStack(spacing: 10) {
                                    ForEach(Array(bullets.enumerated()), id: \.offset) { index, bullet in
                                        HStack(alignment: .top, spacing: 10) {
                                            Text("\(index + 1)")
                                                .font(.caption2)
                                                .fontWeight(.bold)
                                                .padding(5)
                                                .background(Circle().fill(Color.purple.opacity(0.12)))
                                                .foregroundStyle(.purple)
                                                .frame(width: 24, height: 24)

                                            Text(bullet)
                                                .font(.subheadline)
                                                .lineSpacing(3)
                                                .foregroundStyle(.primary)

                                            Spacer()

                                            Button(action: {
                                                NSPasteboard.general.clearContents()
                                                NSPasteboard.general.setString(bullet, forType: .string)
                                                copiedBulletIndex = index
                                                DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                                                    copiedBulletIndex = nil
                                                }
                                            }) {
                                                Image(systemName: copiedBulletIndex == index ? "checkmark" : "doc.on.doc")
                                                    .font(.caption)
                                                    .foregroundStyle(copiedBulletIndex == index ? .green : .secondary)
                                            }
                                            .buttonStyle(.plain)
                                            .help("Copy bullet to clipboard")
                                        }
                                        .padding(12)
                                        .background(Color(NSColor.controlBackgroundColor))
                                        .cornerRadius(8)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 8)
                                                .stroke(Color.secondary.opacity(0.1), lineWidth: 1)
                                        )
                                    }
                                }
                            } else {
                                Text("No automated bullets extracted for this repository yet.")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        // Strategic Context Card
                        VStack(alignment: .leading, spacing: 8) {
                            Label("ATS TAILORING ALIGNMENT", systemImage: "target")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundStyle(.blue)

                            Text("This repository is dynamically evaluated by the ATS Tailor Engine against active job descriptions. When low-level systems, device drivers, or Linux concurrency skills are required, this project's bullets are prioritized to guarantee 100% technical keyword coverage within the strict 52-line single page budget.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineSpacing(2)
                        }
                        .padding(14)
                        .background(Color.blue.opacity(0.06))
                        .cornerRadius(8)
                    }
                    .padding(20)
                }
                .background(Color(NSColor.underPageBackgroundColor))
            }
        } else {
            VStack(spacing: 12) {
                Image(systemName: "curlybraces.square")
                    .font(.system(size: 48))
                    .foregroundStyle(.secondary)
                Text("Select a Repository")
                    .font(.title2)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
                Text("Choose a project from the left pane to view its extracted Google XYZ metrics, commit history, and ATS alignment.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 320)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(NSColor.underPageBackgroundColor))
        }
    }

    private func formatDate(_ dateStr: String) -> String {
        let prefix = String(dateStr.prefix(19))
        let df = DateFormatter()
        df.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        if let d = df.date(from: prefix) {
            let out = DateFormatter()
            out.dateStyle = .medium
            return out.string(from: d)
        }
        return dateStr
    }
}
