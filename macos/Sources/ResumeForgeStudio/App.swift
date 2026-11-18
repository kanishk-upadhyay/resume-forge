import SwiftUI
import AppKit

@main
struct ResumeForgeStudioApp: App {
    @StateObject private var dataManager = DataManager.shared
    @StateObject private var calendarManager = CalendarManager.shared

    var body: some Scene {
        WindowGroup("ResumeForge Studio") {
            MainView()
                .frame(minWidth: 1050, minHeight: 680)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            SidebarCommands()
            CommandGroup(replacing: .newItem) {
                Button("Refresh Applications") {
                    Task { await dataManager.fetchApplications() }
                }
                .keyboardShortcut("r", modifiers: .command)

                Button("Trigger Scout") {
                    Task { await dataManager.triggerScout() }
                }
                .keyboardShortcut("s", modifiers: [.command, .shift])
            }
        }

        MenuBarExtra("ResumeForge", systemImage: "bolt.badge.clock.fill") {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Circle()
                        .fill(dataManager.daemonOnline ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(dataManager.daemonOnline ? "Daemon :5999 Online" : "Daemon Offline")
                        .font(.caption)
                }

                Divider()

                Text("Pipeline Summary:")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text("• Total Tracked: \(dataManager.applications.count)")
                Text("• Discovered: \(dataManager.stats["DISCOVERED"] ?? 0)")
                Text("• Applied: \(dataManager.stats["APPLIED"] ?? 0)")
                Text("• OA Pending: \(dataManager.stats["OA_PENDING"] ?? 0)")

                // Deadlines
                let urgent = dataManager.applications.filter { ($0.daysUntilDeadline ?? 999) <= 3 }
                if !urgent.isEmpty {
                    Divider()
                    Text("⚠️ \(urgent.count) Urgent Deadlines:")
                        .font(.caption2)
                        .foregroundStyle(.red)
                    ForEach(urgent.prefix(3), id: \.id) { app in
                        Text("• \(app.company): \(app.deadlineText)")
                            .font(.caption)
                    }
                }

                Divider()

                Button("Scout New Opportunities Now") {
                    Task { await dataManager.triggerScout() }
                }
                .disabled(dataManager.isScouting)

                Button("Open ResumeForge Studio") {
                    NSApp.activate(ignoringOtherApps: true)
                    if let window = NSApp.windows.first(where: { $0.title == "ResumeForge Studio" }) {
                        window.makeKeyAndOrderFront(nil)
                    }
                }

                Divider()

                Button("Quit ResumeForge") {
                    NSApplication.shared.terminate(nil)
                }
                .keyboardShortcut("q")
            }
            .padding(4)
        }
    }
}
