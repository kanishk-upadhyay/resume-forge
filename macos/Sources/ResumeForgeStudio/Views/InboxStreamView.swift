import SwiftUI
import AppKit

public struct InboxStreamView: View {
    @ObservedObject private var dataManager = DataManager.shared

    public init() {}

    public var body: some View {
        VStack(spacing: 0) {
            // Header Bar
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 8) {
                        Image(systemName: "tray.full.fill")
                            .foregroundStyle(.blue)
                        Text("Thunderbird Inbound Stream")
                            .font(.title2)
                            .fontWeight(.bold)
                    }
                    Text("Passive local Mbox audit • Receipts, OAs, and Interview stages synced automatically")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button(action: {
                    Task {
                        await dataManager.fetchInboxFeed()
                    }
                }) {
                    Label("Refresh Feed", systemImage: "arrow.clockwise")
                }
                .buttonStyle(.bordered)
            }
            .padding(16)
            .background(Color(NSColor.windowBackgroundColor))

            Divider()

            // Feed List
            if dataManager.inboxFeed.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "tray")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No Inbound Emails Detected Yet")
                        .font(.headline)
                        .foregroundStyle(.secondary)
                    Text("As application confirmations and OA test invitations arrive in Mozilla Thunderbird, they will appear here.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: 360)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color(NSColor.underPageBackgroundColor))
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(dataManager.inboxFeed, id: \.id) { email in
                            InboxEmailCard(email: email)
                        }
                    }
                    .padding(16)
                }
                .background(Color(NSColor.underPageBackgroundColor))
            }
        }
    }
}

struct InboxEmailCard: View {
    let email: InboxEmail
    @ObservedObject private var dataManager = DataManager.shared

    private var statusColor: Color {
        switch email.status.uppercased() {
        case "DISCOVERED": return .blue
        case "APPLIED": return .purple
        case "OA_PENDING": return .orange
        case "INTERVIEWING": return .green
        case "OFFER": return .yellow
        case "REJECTED": return .red
        default: return .secondary
        }
    }

    private var statusIcon: String {
        switch email.status.uppercased() {
        case "OA_PENDING": return "bolt.badge.clock.fill"
        case "INTERVIEWING": return "person.2.wave.2.fill"
        case "REJECTED": return "xmark.circle.fill"
        case "APPLIED": return "checkmark.circle.fill"
        default: return "envelope.fill"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                // Status Badge
                HStack(spacing: 4) {
                    Image(systemName: statusIcon)
                    Text(email.status.replacingOccurrences(of: "_", with: " "))
                        .fontWeight(.bold)
                }
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(statusColor.opacity(0.15))
                .foregroundStyle(statusColor)
                .cornerRadius(4)

                Text(email.company)
                    .font(.headline)
                    .fontWeight(.bold)

                Spacer()

                Text(email.date)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Text(email.subject)
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundStyle(.primary)

            HStack {
                Label(email.sender, systemImage: "paperplane")
                    .font(.caption2)
                    .foregroundStyle(.secondary)

                if let reason = email.reason {
                    Text("•")
                        .foregroundStyle(.secondary)
                    Text(reason)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                if let appId = email.app_id, let matched = dataManager.applications.first(where: { $0.id == appId || $0.company.lowercased() == email.company.lowercased() }) {
                    Button(action: {
                        dataManager.selectApplication(matched)
                        dataManager.selectedTab = "APPLICATIONS"
                    }) {
                        HStack(spacing: 4) {
                            Text("View Job")
                            Image(systemName: "arrow.right")
                        }
                        .font(.caption)
                        .fontWeight(.medium)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }
        }
        .padding(12)
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.secondary.opacity(0.15), lineWidth: 1)
        )
    }
}
