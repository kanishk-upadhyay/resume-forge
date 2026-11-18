import SwiftUI

public struct SidebarView: View {
    @ObservedObject private var dataManager = DataManager.shared

    private let statusOptions = [
        ("ALL", "tray.full.fill", Color.primary),
        ("DISCOVERED", "sparkles", Color.blue),
        ("APPLIED", "paperplane.fill", Color.purple),
        ("OA_PENDING", "hourglass", Color.orange),
        ("INTERVIEWING", "person.2.wave.2.fill", Color.green),
        ("REJECTED", "xmark.circle.fill", Color.red)
    ]

    private let categories = [
        ("ALL", "square.grid.2x2", "All Domains"),
        ("F1 / Motorsports", "flag.checkered.2.crossed", "F1 & Motorsports"),
        ("FOSS First", "shippingbox.fill", "Open Source / FOSS"),
        ("General Tech", "laptopcomputer", "Big Tech & Systems")
    ]

    public var body: some View {
        VStack(spacing: 0) {
            List {
                Section(header: Text("WORKFLOW").font(.caption2).fontWeight(.semibold)) {
                    HStack {
                        Label("Applications Pipeline", systemImage: "briefcase.fill")
                        Spacer()
                        Text("\(dataManager.applications.count)")
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(Color(NSColor.quaternaryLabelColor)))
                    }
                    .contentShape(Rectangle())
                    .listRowBackground(dataManager.selectedTab == "APPLICATIONS" ? Color.accentColor.opacity(0.15) : Color.clear)
                    .onTapGesture {
                        dataManager.selectedTab = "APPLICATIONS"
                    }

                    HStack {
                        Label("Inbound Mail Stream", systemImage: "tray.full.fill")
                        Spacer()
                        Text("\(dataManager.inboxFeed.count)")
                            .font(.caption)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(Color(NSColor.quaternaryLabelColor)))
                    }
                    .contentShape(Rectangle())
                    .listRowBackground(dataManager.selectedTab == "INBOX" ? Color.accentColor.opacity(0.15) : Color.clear)
                    .onTapGesture {
                        dataManager.selectedTab = "INBOX"
                    }
                }

                if dataManager.selectedTab == "APPLICATIONS" {
                    Section(header: Text("PIPELINE STAGES").font(.caption2).fontWeight(.semibold)) {
                        ForEach(statusOptions, id: \.0) { key, icon, color in
                            HStack {
                                Label {
                                    Text(key.replacingOccurrences(of: "_", with: " ").capitalized)
                                } icon: {
                                    Image(systemName: icon)
                                        .foregroundStyle(color)
                                }
                                Spacer()
                                Text("\(countForStatus(key))")
                                    .font(.caption)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(Color(NSColor.quaternaryLabelColor)))
                            }
                            .contentShape(Rectangle())
                            .tag(key)
                            .listRowBackground(dataManager.selectedFilter == key ? Color.accentColor.opacity(0.15) : Color.clear)
                            .onTapGesture {
                                dataManager.selectedFilter = key
                            }
                        }
                    }

                    Section(header: Text("DOMAINS & SECTORS").font(.caption2).fontWeight(.semibold)) {
                        ForEach(categories, id: \.0) { catKey, icon, label in
                            HStack {
                                Label(label, systemImage: icon)
                                Spacer()
                                Text("\(countForCategory(catKey))")
                                    .font(.caption)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(Capsule().fill(Color(NSColor.quaternaryLabelColor)))
                            }
                            .contentShape(Rectangle())
                            .tag(catKey)
                            .listRowBackground(dataManager.selectedCategory == catKey ? Color.accentColor.opacity(0.15) : Color.clear)
                            .onTapGesture {
                                dataManager.selectedCategory = catKey
                            }
                        }
                    }
                }
            }
            .listStyle(.sidebar)

            Divider()

            // Footer: Daemon Health & Scout Trigger
            VStack(spacing: 8) {
                HStack {
                    Circle()
                        .fill(dataManager.daemonOnline ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(dataManager.daemonOnline ? "Daemon :5999 Online" : "Daemon Disconnected")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Spacer()
                }

                if let msg = dataManager.statusMessage {
                    Text(msg)
                        .font(.caption2)
                        .foregroundStyle(.green)
                        .lineLimit(1)
                }

                Button(action: {
                    Task { await dataManager.triggerScout() }
                }) {
                    HStack {
                        if dataManager.isScouting {
                            ProgressView().scaleEffect(0.6)
                        } else {
                            Image(systemName: "bolt.fill")
                        }
                        Text("Scout New Roles Now")
                            .fontWeight(.medium)
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
                .disabled(dataManager.isScouting)
            }
            .padding(10)
            .background(Color(NSColor.windowBackgroundColor))
        }
        .frame(minWidth: 200, idealWidth: 220)
    }

    private func countForStatus(_ key: String) -> Int {
        if key == "ALL" {
            return dataManager.applications.count
        }
        return dataManager.stats[key] ?? 0
    }

    private func countForCategory(_ cat: String) -> Int {
        if cat == "ALL" {
            return dataManager.applications.count
        }
        return dataManager.applications.filter { $0.category == cat }.count
    }
}
