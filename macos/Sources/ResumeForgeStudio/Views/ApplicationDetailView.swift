import SwiftUI
import AppKit

public struct ApplicationDetailView: View {
    public let app: Application?

    @ObservedObject private var dataManager = DataManager.shared
    @ObservedObject private var calendarManager = CalendarManager.shared
    @State private var showingDeadlineSheet = false
    @State private var calendarSyncSuccess = false

    public init(app: Application?) {
        self.app = app
    }

    public var body: some View {
        if let app = app {
            VStack(spacing: 0) {
                // Top Header Card
                VStack(alignment: .leading, spacing: 12) {
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack(spacing: 8) {
                                Image(systemName: app.categoryIcon)
                                    .foregroundStyle(.blue)
                                Text(app.company)
                                    .font(.title2)
                                    .fontWeight(.bold)
                            }
                            Text(app.role)
                                .font(.headline)
                                .foregroundStyle(.primary)

                            if let loc = app.location, !loc.isEmpty {
                                Label(loc, systemImage: "mappin.and.ellipse")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        Spacer()

                        // Status Menu Dropdown
                        Menu {
                            ForEach(["DISCOVERED", "APPLIED", "OA_PENDING", "INTERVIEWING", "OFFER", "REJECTED"], id: \.self) { st in
                                Button(action: {
                                    Task { await dataManager.transitionStatus(app: app, to: st) }
                                }) {
                                    HStack {
                                        Text(st.replacingOccurrences(of: "_", with: " "))
                                        if app.status == st {
                                            Image(systemName: "checkmark")
                                        }
                                    }
                                }
                            }
                        } label: {
                            HStack(spacing: 6) {
                                Circle().fill(app.statusColor).frame(width: 8, height: 8)
                                Text(app.status.replacingOccurrences(of: "_", with: " "))
                                    .fontWeight(.semibold)
                                Image(systemName: "chevron.down")
                                    .font(.caption2)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(app.statusColor.opacity(0.15))
                            .foregroundStyle(app.statusColor)
                            .cornerRadius(6)
                        }
                        .menuStyle(.borderlessButton)
                    }

                    // Calendar & Deadline Card
                    HStack {
                        if let deadline = app.effectiveDeadlineString, !deadline.isEmpty {
                            HStack(spacing: 10) {
                                Image(systemName: "calendar.badge.clock")
                                    .font(.title3)
                                    .foregroundStyle(app.deadlineColor)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(app.oa_deadline != nil ? "Online Assessment Due:" : "Application Deadline:")
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                    Text(app.deadlineText)
                                        .font(.subheadline)
                                        .fontWeight(.semibold)
                                        .foregroundStyle(app.deadlineColor)
                                }
                            }

                            Spacer()

                            // Quick Sync Buttons
                            HStack(spacing: 8) {
                                Button(action: {
                                    if let d = app.effectiveDeadlineDate {
                                        Task {
                                            let ok = (try? await calendarManager.addToAppleCalendar(application: app, deadlineDate: d, isOA: app.oa_deadline != nil)) ?? false
                                            if ok { calendarSyncSuccess = true }
                                        }
                                    }
                                }) {
                                    Label("Apple Calendar", systemImage: "calendar")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption)

                                Button(action: {
                                    if let d = app.effectiveDeadlineDate {
                                        calendarManager.openInGoogleCalendar(application: app, deadlineDate: d, isOA: app.oa_deadline != nil)
                                    }
                                }) {
                                    Label("Google Calendar", systemImage: "globe")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption)

                                Button(action: { showingDeadlineSheet = true }) {
                                    Image(systemName: "pencil")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption)
                            }
                        } else {
                            HStack {
                                Image(systemName: "calendar")
                                    .foregroundStyle(.secondary)
                                Text("No deadline recorded for this opening")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Button(action: { showingDeadlineSheet = true }) {
                                    Label("Set Deadline & Calendar Reminder", systemImage: "plus.circle.fill")
                                        .fontWeight(.medium)
                                }
                                .buttonStyle(.borderedProminent)
                                .font(.caption)
                            }
                        }
                    }
                    .padding(10)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(8)

                    // Action Toolbar
                    HStack(spacing: 12) {
                        Button(action: { dataManager.openInZen(url: app.url) }) {
                            Label("Open ATS Portal", systemImage: "safari.fill")
                                .fontWeight(.medium)
                        }
                        .buttonStyle(.borderedProminent)

                        Button(action: { dataManager.openMailto(app: app) }) {
                            Label("1-Click Pitch Email", systemImage: "paperplane.fill")
                        }
                        .buttonStyle(.bordered)

                        if let pdf = app.resume_used, !pdf.isEmpty {
                            Button(action: { dataManager.revealPDF(path: pdf) }) {
                                Label("Reveal PDF", systemImage: "folder.fill")
                            }
                            .buttonStyle(.bordered)
                        }

                        Spacer()

                        if let syncMsg = calendarManager.lastSyncMessage {
                            Text(syncMsg)
                                .font(.caption2)
                                .foregroundStyle(.green)
                        }
                    }
                }
                .padding(16)
                .background(Color(NSColor.windowBackgroundColor))

                Divider()

                // Embedded Interactive PDFKit Preview
                ZStack {
                    if let pdf = app.resume_used, !pdf.isEmpty, FileManager.default.fileExists(atPath: pdf) {
                        PDFPreviewView(pdfPath: pdf)
                    } else {
                        VStack(spacing: 12) {
                            Image(systemName: "doc.text.fill")
                                .font(.system(size: 48))
                                .foregroundStyle(.secondary)
                            Text("Tailored 1-Page PDF Not Found")
                                .font(.headline)
                                .foregroundStyle(.secondary)
                            Text("Run 'Scout Roles Now' in the sidebar to auto-compile this resume.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color(NSColor.underPageBackgroundColor))
                    }
                }
            }
            .sheet(isPresented: $showingDeadlineSheet) {
                DeadlinePickerSheet(application: app, isPresented: $showingDeadlineSheet)
            }
        } else {
            VStack(spacing: 12) {
                Image(systemName: "cursorarrow.and.square.on.square.dashed")
                    .font(.system(size: 48))
                    .foregroundStyle(.secondary)
                Text("Select an Application")
                    .font(.title2)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
                Text("Choose an opening from the list to preview the tailored 1-page resume and manage calendar deadlines.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 320)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}
