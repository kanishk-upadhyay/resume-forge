import Foundation
import AppKit
import EventKit

@MainActor
public final class CalendarManager: ObservableObject {
    public static let shared = CalendarManager()

    private let eventStore = EKEventStore()
    @Published public var hasCalendarAccess: Bool = false
    @Published public var lastSyncMessage: String? = nil

    public init() {
        checkAuthorization()
    }

    public func checkAuthorization() {
        let status = EKEventStore.authorizationStatus(for: .event)
        if #available(macOS 14.0, *) {
            self.hasCalendarAccess = (status == .fullAccess || status == .writeOnly)
        } else {
            self.hasCalendarAccess = (status.rawValue == 3) // 3 corresponds to legacy .authorized
        }
    }

    public func requestAccess() async -> Bool {
        do {
            var granted = false
            #if compiler(>=5.9)
            if #available(macOS 14.0, *) {
                granted = try await eventStore.requestFullAccessToEvents()
            } else {
                granted = try await eventStore.requestAccess(to: .event)
            }
            #else
            granted = try await eventStore.requestAccess(to: .event)
            #endif
            self.hasCalendarAccess = granted
            return granted
        } catch {
            print("Calendar authorization error: \(error)")
            self.hasCalendarAccess = false
            return false
        }
    }

    // MARK: - Native Apple Calendar EventKit Sync

    public func addToAppleCalendar(application: Application, deadlineDate: Date, isOA: Bool) async throws -> Bool {
        let granted = await requestAccess()
        guard granted else {
            // Fallback to Google Calendar or ICS if permission is denied
            openInGoogleCalendar(application: application, deadlineDate: deadlineDate, isOA: isOA)
            return false
        }

        let event = EKEvent(eventStore: eventStore)
        let prefix = isOA ? "📝 [OA Due]" : "🎯 [Application Deadline]"
        event.title = "\(prefix) \(application.company) - \(application.role)"
        event.startDate = deadlineDate
        event.endDate = deadlineDate.addingTimeInterval(3600) // 1-hour block
        event.url = URL(string: application.url)
        event.location = application.location ?? "Online / Remote"

        let resumePath = application.resume_used ?? "Not yet compiled"
        event.notes = """
        Job Opening: \(application.role) at \(application.company)
        Apply Link: \(application.url)
        Tailored Resume: \(resumePath)
        Current Status: \(application.status)
        Tracked via: ResumeForge Studio
        """

        // Smart alerts: 2 days before, 1 day before, and 2 hours before
        event.alarms = [
            EKAlarm(relativeOffset: -48 * 3600),
            EKAlarm(relativeOffset: -24 * 3600),
            EKAlarm(relativeOffset: -2 * 3600)
        ]

        if let defaultCal = eventStore.defaultCalendarForNewEvents {
            event.calendar = defaultCal
        } else {
            let calendars = eventStore.calendars(for: .event)
            event.calendar = calendars.first(where: { $0.allowsContentModifications })
        }

        try eventStore.save(event, span: .thisEvent, commit: true)
        self.lastSyncMessage = "✓ Added to Apple Calendar with 48h and 2h alerts!"
        return true
    }

    // MARK: - Google Calendar Web Deep-Link

    public func openInGoogleCalendar(application: Application, deadlineDate: Date, isOA: Bool) {
        let prefix = isOA ? "[OA Due]" : "[Deadline]"
        let title = "\(prefix) \(application.company) - \(application.role)"
        
        let df = DateFormatter()
        df.timeZone = TimeZone(secondsFromGMT: 0)
        df.dateFormat = "yyyyMMdd'T'HHmmss'Z'"
        
        let startStr = df.string(from: deadlineDate)
        let endStr = df.string(from: deadlineDate.addingTimeInterval(3600))
        
        let details = """
        Role: \(application.role)
        Company: \(application.company)
        Apply URL: \(application.url)
        Resume: \(application.resume_used ?? "Pre-compiled single page PDF")
        """

        var components = URLComponents(string: "https://calendar.google.com/calendar/render")!
        components.queryItems = [
            URLQueryItem(name: "action", value: "TEMPLATE"),
            URLQueryItem(name: "text", value: title),
            URLQueryItem(name: "dates", value: "\(startStr)/\(endStr)"),
            URLQueryItem(name: "details", value: details),
            URLQueryItem(name: "location", value: application.location ?? "Remote / Online")
        ]

        if let gcalURL = components.url {
            NSWorkspace.shared.open(gcalURL)
            self.lastSyncMessage = "✓ Opened in Google Calendar!"
        }
    }

    // MARK: - Universal .ics File Export

    public func exportICS(application: Application, deadlineDate: Date, isOA: Bool) -> URL? {
        let prefix = isOA ? "[OA Due]" : "[Deadline]"
        let title = "\(prefix) \(application.company) - \(application.role)"
        
        let df = DateFormatter()
        df.timeZone = TimeZone(secondsFromGMT: 0)
        df.dateFormat = "yyyyMMdd'T'HHmmss'Z'"
        
        let startStr = df.string(from: deadlineDate)
        let endStr = df.string(from: deadlineDate.addingTimeInterval(3600))
        let nowStr = df.string(from: Date())

        let icsContent = """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:-//ResumeForge//Studio//EN
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        BEGIN:VEVENT
        UID:\(application.id)-\(startStr)@resumeforge
        DTSTAMP:\(nowStr)
        DTSTART:\(startStr)
        DTEND:\(endStr)
        SUMMARY:\(title)
        DESCRIPTION:Apply: \(application.url)\\nTailored Resume: \(application.resume_used ?? "")
        URL:\(application.url)
        LOCATION:\(application.location ?? "Remote")
        BEGIN:VALARM
        TRIGGER:-PT48H
        ACTION:DISPLAY
        DESCRIPTION:Application Deadline in 48 Hours
        END:VALARM
        BEGIN:VALARM
        TRIGGER:-PT2H
        ACTION:DISPLAY
        DESCRIPTION:Application Deadline in 2 Hours!
        END:VALARM
        END:VEVENT
        END:VCALENDAR
        """

        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("\(application.id)_deadline.ics")
        do {
            try icsContent.write(to: tempURL, atomically: true, encoding: .utf8)
            NSWorkspace.shared.open(tempURL)
            self.lastSyncMessage = "✓ Exported .ics and opened Calendar!"
            return tempURL
        } catch {
            print("Failed to write ICS file: \(error)")
            return nil
        }
    }
}
