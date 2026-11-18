import SwiftUI

public struct ApplicationListView: View {
    @ObservedObject private var dataManager = DataManager.shared
    @State private var showingDeadlineSheet = false
    @State private var targetAppForDeadline: Application?

    public var body: some View {
        VStack(spacing: 0) {
            // Search Bar & Stats Header
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search companies, roles, cities...", text: $dataManager.searchText)
                    .textFieldStyle(.plain)
                if !dataManager.searchText.isEmpty {
                    Button(action: { dataManager.searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
            .padding(10)

            Divider()

            // List of applications
            if dataManager.filteredApplications.isEmpty {
                VStack(spacing: 12) {
                    Spacer()
                    Image(systemName: "tray")
                        .font(.system(size: 36))
                        .foregroundStyle(.secondary)
                    Text("No Applications Found")
                        .font(.headline)
                        .foregroundStyle(.secondary)
                    Text("Try clearing search or click 'Scout Roles Now'")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
            } else {
                List(dataManager.filteredApplications, id: \.id, selection: $dataManager.selectedApp) { app in
                    ApplicationRow(app: app, onSetDeadline: {
                        targetAppForDeadline = app
                        showingDeadlineSheet = true
                    })
                    .tag(app)
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
            }
        }
        .frame(minWidth: 320, idealWidth: 360)
        .sheet(item: $targetAppForDeadline) { app in
            DeadlinePickerSheet(application: app, isPresented: $showingDeadlineSheet)
        }
    }
}

private struct ApplicationRow: View {
    let app: Application
    let onSetDeadline: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 6) {
                        Image(systemName: app.categoryIcon)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text(app.company)
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    Text(app.role)
                        .font(.subheadline)
                        .foregroundStyle(.primary)
                        .lineLimit(1)
                }
                Spacer()

                // Status Badge
                Text(app.status.replacingOccurrences(of: "_", with: " "))
                    .font(.system(size: 10, weight: .bold))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(app.statusColor.opacity(0.18))
                    .foregroundStyle(app.statusColor)
                    .clipShape(Capsule())
            }

            // Location & Deadline Info
            HStack(spacing: 10) {
                if let loc = app.location, !loc.isEmpty {
                    Label(loc, systemImage: "mappin.and.ellipse")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }

                Spacer()

                // Deadline Pill
                if app.effectiveDeadlineString != nil {
                    HStack(spacing: 4) {
                        Image(systemName: "calendar.badge.clock")
                        Text(app.deadlineText)
                    }
                    .font(.system(size: 10, weight: .medium))
                    .foregroundStyle(app.deadlineColor)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(app.deadlineColor.opacity(0.12))
                    .cornerRadius(4)
                } else {
                    Button(action: onSetDeadline) {
                        HStack(spacing: 3) {
                            Image(systemName: "plus.circle")
                            Text("Deadline")
                        }
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}
