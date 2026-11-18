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
                VStack(alignment: .leading, spacing: 10) {
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

                    // 1. Live OA Countdown Sentinel Banner (if OA_PENDING)
                    if app.isOAPending {
                        HStack(spacing: 10) {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 10, height: 10)
                            
                            VStack(alignment: .leading, spacing: 2) {
                                Text("🔴 Live Online Assessment Countdown")
                                    .font(.caption2)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.red)
                                Text(app.oaCountdownFormatted)
                                    .font(.subheadline)
                                    .fontWeight(.heavy)
                                    .foregroundStyle(.primary)
                            }

                            Spacer()

                            if let d = app.effectiveDeadlineDate {
                                Button(action: {
                                    Task {
                                        _ = try? await calendarManager.addToAppleCalendar(application: app, deadlineDate: d, isOA: true)
                                    }
                                }) {
                                    Label("Sync 48h/2h Alerts", systemImage: "bell.badge.fill")
                                        .font(.caption)
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                        .padding(10)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.red.opacity(0.3), lineWidth: 1)
                        )
                    }

                    // 2. 7-Day Ghosting Sentinel Banner (if APPLIED >= 7 days)
                    if app.isGhosting {
                        HStack(spacing: 10) {
                            Image(systemName: "clock.badge.exclamationmark.fill")
                                .font(.title3)
                                .foregroundStyle(.orange)

                            VStack(alignment: .leading, spacing: 2) {
                                Text("⚠️ Ghosting Sentinel: No Response in \(app.daysSinceApplied ?? 7) Days")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.orange)
                                Text("Applied on \(app.date_applied ?? "unknown"). Time for a gentle technical bump.")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }

                            Spacer()

                            Button(action: {
                                dataManager.openFollowUp(app: app)
                            }) {
                                Label("⚡ 1-Click Send Follow-Up Ping", systemImage: "paperplane.fill")
                                    .fontWeight(.semibold)
                                    .font(.caption)
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.orange)
                        }
                        .padding(10)
                        .background(Color.orange.opacity(0.12))
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.orange.opacity(0.3), lineWidth: 1)
                        )
                    }

                    // 3. ATS Match Radar & Auto-Tailor Card
                    ATSScoreCardView(app: app)

                    // 4. Calendar & Deadline Row
                    HStack {
                        if let deadline = app.effectiveDeadlineString, !deadline.isEmpty {
                            HStack(spacing: 8) {
                                Image(systemName: "calendar.badge.clock")
                                    .foregroundStyle(app.deadlineColor)
                                Text(app.deadlineText)
                                    .font(.caption)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(app.deadlineColor)
                            }

                            Spacer()

                            HStack(spacing: 6) {
                                Button(action: {
                                    if let d = app.effectiveDeadlineDate {
                                        Task {
                                            let ok = (try? await calendarManager.addToAppleCalendar(application: app, deadlineDate: d, isOA: app.oa_deadline != nil)) ?? false
                                            if ok { calendarSyncSuccess = true }
                                        }
                                    }
                                }) {
                                    Label("Apple Cal", systemImage: "calendar")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption2)

                                Button(action: {
                                    if let d = app.effectiveDeadlineDate {
                                        calendarManager.openInGoogleCalendar(application: app, deadlineDate: d, isOA: app.oa_deadline != nil)
                                    }
                                }) {
                                    Label("Google Cal", systemImage: "globe")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption2)

                                Button(action: { showingDeadlineSheet = true }) {
                                    Image(systemName: "pencil")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption2)
                            }
                        } else {
                            HStack {
                                Image(systemName: "calendar")
                                    .foregroundStyle(.secondary)
                                Text("No deadline recorded")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Button(action: { showingDeadlineSheet = true }) {
                                    Label("Set Deadline", systemImage: "plus.circle.fill")
                                }
                                .buttonStyle(.bordered)
                                .font(.caption2)
                            }
                        }
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color(NSColor.controlBackgroundColor).opacity(0.4))
                    .cornerRadius(6)

                    // Action Toolbar
                    HStack(spacing: 10) {
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
                .padding(14)
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
                            Text("Click '✨ Auto-Tailor Bullets' above to compile a 1-page PDF for this role.")
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
                Text("Choose an opening from the list to preview the tailored 1-page resume and audit ATS match keywords.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 320)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}
