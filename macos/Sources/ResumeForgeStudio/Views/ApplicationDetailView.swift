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
                // Top Control Pane
                VStack(alignment: .leading, spacing: 10) {
                    // 1. Header Bar: Identity + Status Dropdown + Primary Portal Action
                    HStack(alignment: .center) {
                        VStack(alignment: .leading, spacing: 3) {
                            HStack(spacing: 8) {
                                Image(systemName: app.categoryIcon)
                                    .font(.title3)
                                    .foregroundStyle(.blue)
                                Text(app.company)
                                    .font(.title2)
                                    .fontWeight(.bold)
                            }
                            HStack(spacing: 8) {
                                Text(app.role)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                    .foregroundStyle(.primary)

                                if let loc = app.location, !loc.isEmpty {
                                    Text("•")
                                        .foregroundStyle(.secondary)
                                    Label(loc, systemImage: "mappin.and.ellipse")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }

                        Spacer()

                        // Status Picker + Primary "Open Portal" Action
                        HStack(spacing: 10) {
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
                                .padding(.vertical, 6)
                                .background(app.statusColor.opacity(0.15))
                                .foregroundStyle(app.statusColor)
                                .cornerRadius(6)
                            }
                            .menuStyle(.borderlessButton)

                            // Primary Call-To-Action Button
                            Button(action: { dataManager.openInZen(url: app.url) }) {
                                Label("Open ATS Portal", systemImage: "arrow.up.right.square.fill")
                                    .fontWeight(.semibold)
                            }
                            .buttonStyle(.borderedProminent)
                        }
                    }

                    // 2. Unified Context & Quick Actions Bar
                    HStack(spacing: 8) {
                        // Live OA Countdown Pill (if OA_PENDING)
                        if app.isOAPending {
                            HStack(spacing: 5) {
                                Circle().fill(Color.red).frame(width: 7, height: 7)
                                Text("OA: \(app.oaCountdownFormatted)")
                                    .font(.caption2)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.red)

                                if let d = app.effectiveDeadlineDate {
                                    Button(action: {
                                        Task {
                                            _ = try? await calendarManager.addToAppleCalendar(application: app, deadlineDate: d, isOA: true)
                                        }
                                    }) {
                                        Image(systemName: "bell.badge.fill")
                                            .font(.system(size: 9))
                                            .foregroundStyle(.red)
                                    }
                                    .buttonStyle(.plain)
                                    .help("Sync 48h/2h alerts to Apple Calendar")
                                }
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.red.opacity(0.12))
                            .cornerRadius(6)
                        }

                        // Ghosting Sentinel Pill (if APPLIED >= 7 days)
                        if app.isGhosting {
                            HStack(spacing: 5) {
                                Text("👻 \(app.daysSinceApplied ?? 7)d ghosting")
                                    .font(.caption2)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(.orange)

                                Button(action: { dataManager.openFollowUp(app: app) }) {
                                    Image(systemName: "paperplane.fill")
                                        .font(.system(size: 9))
                                        .foregroundStyle(.orange)
                                }
                                .buttonStyle(.plain)
                                .help("Open follow-up email in default mail client")
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.orange.opacity(0.12))
                            .cornerRadius(6)
                        }

                        // Deadline Badge / Editor
                        Button(action: { showingDeadlineSheet = true }) {
                            HStack(spacing: 4) {
                                Image(systemName: "calendar")
                                    .font(.caption2)
                                    .foregroundStyle(app.deadlineColor)
                                Text(app.deadlineText)
                                    .font(.caption2)
                                    .fontWeight(.medium)
                                    .foregroundStyle(app.deadlineColor)
                                Image(systemName: "pencil")
                                    .font(.system(size: 8))
                                    .foregroundStyle(.secondary)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.secondary.opacity(0.1))
                            .cornerRadius(6)
                        }
                        .buttonStyle(.plain)
                        .help("Set or edit application / assessment deadline")

                        Spacer()

                        // Secondary Action Buttons Group
                        HStack(spacing: 6) {
                            Button(action: { dataManager.openMailto(app: app) }) {
                                Label("Pitch Email", systemImage: "paperplane")
                                    .font(.caption)
                            }
                            .buttonStyle(.bordered)
                            .help("Draft 1-click recruiter pitch email")

                            if let pdf = app.resume_used, !pdf.isEmpty {
                                Button(action: { dataManager.revealPDF(path: pdf) }) {
                                    Label("Reveal PDF", systemImage: "folder")
                                        .font(.caption)
                                }
                                .buttonStyle(.bordered)
                                .help("Reveal compiled 1-page PDF in macOS Finder")
                            }

                            // Calendar Quick-Sync Menu
                            Menu {
                                Button("Sync to Apple Calendar") {
                                    if let d = app.effectiveDeadlineDate {
                                        Task {
                                            _ = try? await calendarManager.addToAppleCalendar(application: app, deadlineDate: d, isOA: app.oa_deadline != nil)
                                        }
                                    }
                                }
                                Button("Sync to Google Calendar") {
                                    if let d = app.effectiveDeadlineDate {
                                        calendarManager.openInGoogleCalendar(application: app, deadlineDate: d, isOA: app.oa_deadline != nil)
                                    }
                                }
                            } label: {
                                Image(systemName: "calendar.badge.plus")
                                    .font(.caption)
                            }
                            .menuStyle(.borderlessButton)
                            .frame(width: 24, height: 24)
                            .help("Add deadlines to Apple or Google Calendar")

                            // ATS Inspector Toggle Button
                            Button(action: {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    dataManager.showInspector.toggle()
                                }
                            }) {
                                HStack(spacing: 4) {
                                    Image(systemName: "gauge.with.needle.fill")
                                        .foregroundStyle(dataManager.showInspector ? Color.purple : Color.secondary)
                                    Text("ATS Inspector")
                                        .font(.caption)
                                        .fontWeight(dataManager.showInspector ? .bold : .medium)
                                }
                                .padding(.horizontal, 7)
                                .padding(.vertical, 3.5)
                                .background(dataManager.showInspector ? Color.purple.opacity(0.15) : Color.secondary.opacity(0.1))
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                            .keyboardShortcut("i", modifiers: [.command])
                            .help("Toggle ATS Match Inspector (⌘I)")
                        }
                    }
                }
                .padding(14)
                .background(Color(NSColor.windowBackgroundColor))

                Divider()

                // 3. Embedded Interactive PDFKit Canvas (Full Viewport Height)
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
                            Text("Click '⚡ One-Click ATS Boost' in the ATS Inspector to compile a 1-page PDF for this role.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color(NSColor.underPageBackgroundColor))
                    }
                }
            }
            .inspector(isPresented: $dataManager.showInspector) {
                ATSInspectorView(app: app)
                    .inspectorColumnWidth(min: 280, ideal: 330, max: 400)
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
