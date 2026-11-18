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
    @Published public var searchText: String = ""
    @Published public var isScouting: Bool = false
    @Published public var daemonOnline: Bool = false
    @Published public var stats: [String: Int] = [:]
    @Published public var statusMessage: String? = nil

    private let baseURL = URL(string: "http://127.0.0.1:5999")!
    private var timer: Timer?

    public init() {
        Task {
            await fetchApplications()
        }
        startPolling()
    }

    public func startPolling() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.fetchApplications(silent: true)
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
                self.selectedApp = self.applications.first
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
                // Wait briefly and poll
                try await Task.sleep(nanoseconds: 5_000_000_000)
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

    public func revealPDF(path: String) {
        guard !path.isEmpty && FileManager.default.fileExists(atPath: path) else { return }
        NSWorkspace.shared.selectFile(path, inFileViewerRootedAtPath: "")
    }
}
