import Foundation
import AppKit
import SwiftUI

@MainActor
public final class DataManager: ObservableObject {
    public static let shared = DataManager()

    @Published public var applications: [Application] = []
    @Published public var selectedApp: Application? = nil
    @Published public var selectedFilter: String = "ALL"
    @Published public var selectedCategory: String = "ALL"
    @Published public var selectedTab: String = "APPLICATIONS" // "APPLICATIONS", "INBOX", or "GITHUB"
    @Published public var searchText: String = ""
    @Published public var showInspector: Bool = true
    @Published public var isScouting: Bool = false
    @Published public var isTailoring: Bool = false
    @Published public var isATSLoading: Bool = false
    @Published public var isSyncingGitHub: Bool = false
    @Published public var daemonOnline: Bool = false
    @Published public var stats: [String: Int] = [:]
    @Published public var statusMessage: String? = nil
    @Published public var errorMessage: String? = nil
    @Published public var currentATSResult: ATSResult? = nil
    @Published public var inboxFeed: [InboxEmail] = []
    @Published public var githubRepos: [GitHubRepo] = []
    @Published public var selectedRepo: GitHubRepo? = nil
    @Published public var githubLastScanned: String? = nil
    @Published public var currentTime: Date = Date()

    private let baseURL = URL(string: "http://127.0.0.1:5999")!
    private var pollTimer: Timer?
    private var clockTimer: Timer?

    public init() {
        Task {
            await fetchApplications()
            await fetchInboxFeed()
            await fetchGitHubRepos()
        }
        startPolling()
        startClock()
    }

    public func startPolling() {
        pollTimer?.invalidate()
        pollTimer = Timer.scheduledTimer(withTimeInterval: 4.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.fetchApplications(silent: true)
                await self?.fetchInboxFeed()
            }
        }
    }

    public func startClock() {
        clockTimer?.invalidate()
        clockTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.currentTime = Date()
            }
        }
    }

    // MARK: - API Calls

    public func fetchApplications(silent: Bool = false) async {
        let endpoint = baseURL.appendingPathComponent("api/applications")
        do {
            let (data, response) = try await URLSession.shared.data(from: endpoint)
            guard let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 else {
                self.daemonOnline = false
                return
            }
            self.daemonOnline = true

            struct ResponseData: Codable {
                let status: String
                let applications: [Application]
                let stats: StatsData
            }
            struct StatsData: Codable {
                let total: Int
                let by_status: [String: Int]
            }

            let decoded = try JSONDecoder().decode(ResponseData.self, from: data)
            self.applications = decoded.applications
            self.stats = decoded.stats.by_status
            
            if self.selectedApp == nil && !self.applications.isEmpty {
                self.selectApplication(self.applications.first)
            } else if let sel = self.selectedApp, let updated = self.applications.first(where: { $0.id == sel.id }) {
                self.selectedApp = updated
            }
        } catch {
            if !silent {
                print("Failed to fetch from daemon: \(error)")
            }
            self.daemonOnline = false
        }
    }

    public func selectApplication(_ app: Application?) {
        self.selectedApp = app
        if let app = app {
            Task {
                await fetchATSScore(for: app)
            }
        }
    }

    public func fetchATSScore(for app: Application) async {
        self.isATSLoading = true
        self.errorMessage = nil
        let endpoint = baseURL.appendingPathComponent("api/ats_match")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = ["id": app.id]
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (data, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse {
                if http.statusCode == 200 {
                    let decoded = try JSONDecoder().decode(ATSResult.self, from: data)
                    self.currentATSResult = decoded
                } else {
                    if let errDict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let msg = errDict["message"] as? String ?? errDict["error"] as? String {
                        self.errorMessage = msg
                    } else {
                        self.errorMessage = "Failed to calculate ATS match (HTTP \(http.statusCode))"
                    }
                }
            }
        } catch {
            print("Error fetching ATS match: \(error)")
            self.errorMessage = "Daemon unreachable: \(error.localizedDescription)"
        }
        self.isATSLoading = false
    }

    public func autoTailor(for app: Application, injectKeywords: [String]? = nil, customJD: String? = nil) async {
        self.isTailoring = true
        self.errorMessage = nil
        self.statusMessage = "✨ Boosting ATS score & compiling 1-page PDF..."
        let endpoint = baseURL.appendingPathComponent("api/auto_tailor")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var payload: [String: Any] = ["id": app.id]
        if let kws = injectKeywords, !kws.isEmpty {
            payload["inject_keywords"] = kws
        }
        if let jd = customJD, !jd.isEmpty {
            payload["job_description"] = jd
        }

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (data, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse {
                if http.statusCode == 200 {
                    let decoded = try JSONDecoder().decode(ATSResult.self, from: data)
                    self.currentATSResult = decoded
                    let timeMs = decoded.compilation_time_ms ?? 0
                    self.statusMessage = "✓ ATS Score Boosted to \(decoded.match_rate_percent)% in \(Double(timeMs) / 1000.0)s!"
                    await fetchApplications(silent: true)
                } else {
                    if let errDict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let msg = errDict["message"] as? String ?? errDict["error"] as? String {
                        self.errorMessage = msg
                        self.statusMessage = "❌ Tailoring error: \(msg)"
                    } else {
                        self.errorMessage = "Auto-tailor compile failed (HTTP \(http.statusCode))"
                        self.statusMessage = "❌ Auto-tailor failed (HTTP \(http.statusCode))"
                    }
                }
            }
        } catch {
            self.errorMessage = "Network error: \(error.localizedDescription)"
            self.statusMessage = "❌ Error: \(error.localizedDescription)"
        }
        self.isTailoring = false
    }

    public func injectKeyword(app: Application, keyword: String) async {
        self.isTailoring = true
        self.errorMessage = nil
        self.statusMessage = "⚡ Injecting keyword '\(keyword)' & recompiling..."
        let endpoint = baseURL.appendingPathComponent("api/ats_inject_keyword")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = ["id": app.id, "keyword": keyword]
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (data, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse {
                if http.statusCode == 200 {
                    let decoded = try JSONDecoder().decode(ATSResult.self, from: data)
                    self.currentATSResult = decoded
                    let timeMs = decoded.compilation_time_ms ?? 0
                    self.statusMessage = "✓ Injected '\(keyword)'! Score: \(decoded.match_rate_percent)% (⚡ \(Double(timeMs) / 1000.0)s)"
                    await fetchApplications(silent: true)
                } else {
                    if let errDict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let msg = errDict["message"] as? String ?? errDict["error"] as? String {
                        self.errorMessage = msg
                        self.statusMessage = "❌ Injection failed: \(msg)"
                    } else {
                        self.errorMessage = "Failed to inject keyword (HTTP \(http.statusCode))"
                        self.statusMessage = "❌ Injection failed (HTTP \(http.statusCode))"
                    }
                }
            }
        } catch {
            self.errorMessage = "Network error: \(error.localizedDescription)"
            self.statusMessage = "❌ Injection failed: \(error.localizedDescription)"
        }
        self.isTailoring = false
    }

    public func removeKeyword(app: Application, keyword: String) async {
        self.isTailoring = true
        self.errorMessage = nil
        self.statusMessage = "🗑️ Removing keyword '\(keyword)' & recompiling..."
        let endpoint = baseURL.appendingPathComponent("api/ats_remove_keyword")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = ["id": app.id, "keyword": keyword]
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (data, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse {
                if http.statusCode == 200 {
                    let decoded = try JSONDecoder().decode(ATSResult.self, from: data)
                    self.currentATSResult = decoded
                    let timeMs = decoded.compilation_time_ms ?? 0
                    self.statusMessage = "✓ Removed '\(keyword)'! Score: \(decoded.match_rate_percent)% (⚡ \(Double(timeMs) / 1000.0)s)"
                    await fetchApplications(silent: true)
                } else {
                    if let errDict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let msg = errDict["message"] as? String ?? errDict["error"] as? String {
                        self.errorMessage = msg
                        self.statusMessage = "❌ Removal failed: \(msg)"
                    } else {
                        self.errorMessage = "Failed to remove keyword (HTTP \(http.statusCode))"
                        self.statusMessage = "❌ Removal failed (HTTP \(http.statusCode))"
                    }
                }
            }
        } catch {
            self.errorMessage = "Network error: \(error.localizedDescription)"
            self.statusMessage = "❌ Removal failed: \(error.localizedDescription)"
        }
        self.isTailoring = false
    }

    public func updateJobDescription(app: Application, jd: String) async {
        self.isTailoring = true
        self.errorMessage = nil
        self.statusMessage = "📝 Applying custom JD & re-scoring..."
        let endpoint = baseURL.appendingPathComponent("api/application/update_jd")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = ["id": app.id, "job_description": jd]
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (data, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse {
                if http.statusCode == 200 {
                    let decoded = try JSONDecoder().decode(ATSResult.self, from: data)
                    self.currentATSResult = decoded
                    self.statusMessage = "✓ Custom JD applied! ATS Match: \(decoded.match_rate_percent)%"
                    await fetchApplications(silent: true)
                } else {
                    if let errDict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let msg = errDict["message"] as? String ?? errDict["error"] as? String {
                        self.errorMessage = msg
                        self.statusMessage = "❌ Custom JD failed: \(msg)"
                    } else {
                        self.errorMessage = "Failed to update JD (HTTP \(http.statusCode))"
                        self.statusMessage = "❌ Custom JD failed (HTTP \(http.statusCode))"
                    }
                }
            }
        } catch {
            self.errorMessage = "Network error: \(error.localizedDescription)"
            self.statusMessage = "❌ Update failed: \(error.localizedDescription)"
        }
        self.isTailoring = false
    }

    public func fetchInboxFeed() async {
        let endpoint = baseURL.appendingPathComponent("api/inbox")
        do {
            let (data, response) = try await URLSession.shared.data(from: endpoint)
            guard let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 else { return }

            struct InboxResponse: Codable {
                let status: String
                let feed: [InboxEmail]
            }

            let decoded = try JSONDecoder().decode(InboxResponse.self, from: data)
            self.inboxFeed = decoded.feed
        } catch {
            // Non-critical
        }
    }

    public func fetchGitHubRepos() async {
        let endpoint = baseURL.appendingPathComponent("api/github/repos")
        do {
            let (data, response) = try await URLSession.shared.data(from: endpoint)
            guard let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 else { return }
            let decoded = try JSONDecoder().decode(GitHubReposResponse.self, from: data)
            self.githubRepos = decoded.data.projects
            self.githubLastScanned = decoded.data.last_scanned
            if self.selectedRepo == nil && !self.githubRepos.isEmpty {
                self.selectedRepo = self.githubRepos.first
            }
        } catch {
            print("Error fetching github repos: \(error)")
        }
    }

    public func triggerGitHubScan() async {
        self.isSyncingGitHub = true
        self.statusMessage = "🔍 Scanning GitHub account for new projects & commits..."
        let endpoint = baseURL.appendingPathComponent("api/github/scan")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        do {
            let (_, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse, http.statusCode == 200 {
                self.statusMessage = "✓ GitHub context crawler synced!"
                await fetchGitHubRepos()
                if let sel = self.selectedApp {
                    await fetchATSScore(for: sel)
                }
            }
        } catch {
            print("Error triggering github scan: \(error)")
        }
        self.isSyncingGitHub = false
    }

    public func transitionStatus(app: Application, to newStatus: String) async {
        let endpoint = baseURL.appendingPathComponent("api/transition")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "id": app.id,
            "url": app.url,
            "company": app.company,
            "role": app.role,
            "status": newStatus.uppercased()
        ]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (_, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse, http.statusCode == 200 {
                self.statusMessage = "✓ Marked as \(newStatus.uppercased())"
                await fetchApplications()
            }
        } catch {
            print("Error transitioning status: \(error)")
        }
    }

    public func setDeadline(app: Application, dateString: String, isOA: Bool) async {
        let endpoint = baseURL.appendingPathComponent("api/deadline")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "id": app.id,
            "deadline": dateString,
            "type": isOA ? "oa" : "application"
        ]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (_, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse, http.statusCode == 200 {
                self.statusMessage = "✓ Deadline saved for \(app.company)"
                await fetchApplications()
            }
        } catch {
            print("Error saving deadline: \(error)")
        }
    }

    public func triggerScout() async {
        self.isScouting = true
        self.statusMessage = "⚡ Scouring ATS feeds & compiling PDFs..."
        let endpoint = baseURL.appendingPathComponent("api/scout")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"

        do {
            let (_, resp) = try await URLSession.shared.data(for: request)
            if let http = resp as? HTTPURLResponse, http.statusCode == 200 {
                try await Task.sleep(nanoseconds: 4_000_000_000)
                await fetchApplications()
                self.statusMessage = "✓ Scout complete!"
            }
        } catch {
            print("Error triggering scout: \(error)")
        }
        self.isScouting = false
    }

    // MARK: - Filtering

    public var filteredApplications: [Application] {
        var list = applications

        // Status Filter
        if selectedFilter != "ALL" {
            list = list.filter { $0.status.uppercased() == selectedFilter.uppercased() }
        }

        // Category Filter
        if selectedCategory != "ALL" {
            list = list.filter { $0.category == selectedCategory }
        }

        // Search Filter
        if !searchText.isEmpty {
            let q = searchText.lowercased()
            list = list.filter {
                $0.company.lowercased().contains(q) ||
                $0.role.lowercased().contains(q) ||
                ($0.location?.lowercased().contains(q) ?? false)
            }
        }

        // Sort: Urgent deadlines first, then newest
        return list.sorted { a, b in
            if let da = a.daysUntilDeadline, let db = b.daysUntilDeadline {
                return da < db
            }
            if a.daysUntilDeadline != nil { return true }
            if b.daysUntilDeadline != nil { return false }
            return (a.date_discovered ?? "") > (b.date_discovered ?? "")
        }
    }

    public func openInZen(url: String) {
        guard let u = URL(string: url) else { return }
        NSWorkspace.shared.open(u)
    }

    public func openMailto(app: Application) {
        guard let u = app.mailtoURL else { return }
        NSWorkspace.shared.open(u)
    }

    public func openFollowUp(app: Application) {
        guard let u = app.followUpMailtoURL else { return }
        NSWorkspace.shared.open(u)
    }

    public func revealPDF(path: String) {
        guard !path.isEmpty && FileManager.default.fileExists(atPath: path) else { return }
        NSWorkspace.shared.selectFile(path, inFileViewerRootedAtPath: "")
    }
}
