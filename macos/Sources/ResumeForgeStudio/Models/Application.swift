import Foundation
import SwiftUI

public struct Application: Identifiable, Codable, Hashable {
    public let id: String
    public let company: String
    public let role: String
    public let url: String
    public let location: String?
    public var status: String
    public let date_discovered: String?
    public var date_applied: String?
    public var confirmation_url: String?
    public var candidate_id: String?
    public var oa_deadline: String?
    public var deadline: String?
    public var resume_used: String?
    public var notes: String?

    public init(
        id: String,
        company: String,
        role: String,
        url: String,
        location: String? = nil,
        status: String = "DISCOVERED",
        date_discovered: String? = nil,
        date_applied: String? = nil,
        confirmation_url: String? = nil,
        candidate_id: String? = nil,
        oa_deadline: String? = nil,
        deadline: String? = nil,
        resume_used: String? = nil,
        notes: String? = nil
    ) {
        self.id = id
        self.company = company
        self.role = role
        self.url = url
        self.location = location
        self.status = status
        self.date_discovered = date_discovered
        self.date_applied = date_applied
        self.confirmation_url = confirmation_url
        self.candidate_id = candidate_id
        self.oa_deadline = oa_deadline
        self.deadline = deadline
        self.resume_used = resume_used
        self.notes = notes
    }

    // MARK: - Computed Properties

    public var effectiveDeadlineString: String? {
        oa_deadline ?? deadline
    }

    public var effectiveDeadlineDate: Date? {
        guard let s = effectiveDeadlineString, !s.isEmpty else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withFullDate]
        if let d = formatter.date(from: s) { return d }
        
        let standard = DateFormatter()
        standard.dateFormat = "yyyy-MM-dd"
        if let d = standard.date(from: s) { return d }
        
        standard.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        return standard.date(from: s)
    }

    public var daysUntilDeadline: Int? {
        guard let date = effectiveDeadlineDate else { return nil }
        let calendar = Calendar.current
        let startOfToday = calendar.startOfDay(for: Date())
        let startOfTarget = calendar.startOfDay(for: date)
        let components = calendar.dateComponents([.day], from: startOfToday, to: startOfTarget)
        return components.day
    }

    public var deadlineText: String {
        guard let days = daysUntilDeadline, let date = effectiveDeadlineDate else {
            return "No deadline set"
        }
        let df = DateFormatter()
        df.dateFormat = "MMM d"
        let dateStr = df.string(from: date)

        if days < 0 {
            return "Expired (\(dateStr))"
        } else if days == 0 {
            return "Due today!"
        } else if days == 1 {
            return "Due tomorrow"
        } else if days <= 3 {
            return "\(days) days left (\(dateStr))"
        } else {
            return "\(dateStr) (\(days)d left)"
        }
    }

    public var deadlineColor: Color {
        guard let days = daysUntilDeadline else { return .secondary }
        if days < 0 { return .gray }
        if days <= 2 { return .red }
        if days <= 5 { return .orange }
        return .green
    }

    public var category: String {
        let c = company.lowercased()
        if c.contains("red bull") || c.contains("williams") || c.contains("aston martin") ||
           c.contains("mclaren") || c.contains("ferrari") || c.contains("mercedes") || c.contains("racing") {
            return "F1 / Motorsports"
        }
        if c.contains("canonical") || c.contains("gitlab") || c.contains("mozilla") ||
           c.contains("wikimedia") || c.contains("foss") || c.contains("redhat") {
            return "FOSS First"
        }
        return "General Tech"
    }

    public var categoryIcon: String {
        switch category {
        case "F1 / Motorsports": return "flag.checkered.2.crossed"
        case "FOSS First": return "shippingbox.fill"
        default: return "laptopcomputer"
        }
    }

    public var statusColor: Color {
        switch status.uppercased() {
        case "DISCOVERED": return .blue
        case "APPLIED": return .purple
        case "OA_PENDING": return .orange
        case "INTERVIEWING": return .green
        case "OFFER": return .yellow
        case "REJECTED": return .red
        default: return .secondary
        }
    }

    public var mailtoURL: URL? {
        let subject = "SWE Intern 2027 / Kanishk Upadhyay (GitLab & Open Source Contributor)"
        let body = """
        Hi \(company) team,

        I came across your opening for the \(role) role and wanted to reach out directly.

        I'm a pre-final year CS undergraduate (Class of 2027) with zero university attendance constraints and strong systems foundations:
        • Engineered macOS user-space RNDIS driver in C++23/Swift/libusb (TetherKit) with adaptive polling, slashing CPU from 100.5% to 0.1%.
        • Patched multithreaded concurrency race condition in Apple swift-log and administered Linux VPS daemons with Nginx & systemd.
        • Contributed upstream to core GitLab monorepo across enterprise UI and CI workflows (MR !179636, MR !179628).

        I am available for full-time 3-month summer or 6-month off-cycle engineering internships (zero visa friction—paid as an international contractor via Deel / Wise for remote roles).

        Would love to send over my 1-page resume or contribute a small PR to your codebase.

        Best regards,
        Kanishk Upadhyay
        GitHub: https://github.com/kanishk-upadhyay
        Portfolio: https://kanishk-upadhyay.github.io/
        Email: code.latter678@aleeas.com | Phone: +91 7772034062
        """

        var components = URLComponents()
        components.scheme = "mailto"
        components.path = "careers@\(company.lowercased().filter { $0.isLetter }).com"
        components.queryItems = [
            URLQueryItem(name: "subject", value: subject),
            URLQueryItem(name: "body", value: body)
        ]
        return components.url
    }
}
