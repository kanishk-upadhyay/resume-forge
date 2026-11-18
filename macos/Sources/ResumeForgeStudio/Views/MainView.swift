import SwiftUI

public struct MainView: View {
    @ObservedObject private var dataManager = DataManager.shared

    public init() {}

    public var body: some View {
        NavigationSplitView {
            SidebarView()
        } content: {
            if dataManager.selectedTab == "INBOX" {
                InboxStreamView()
            } else {
                ApplicationListView()
            }
        } detail: {
            ApplicationDetailView(app: dataManager.selectedApp)
        }
        .navigationSplitViewStyle(.balanced)
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button(action: {
                    Task {
                        await dataManager.fetchApplications()
                        await dataManager.fetchInboxFeed()
                    }
                }) {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
            }

            ToolbarItem(placement: .automatic) {
                Button(action: {
                    Task { await dataManager.triggerScout() }
                }) {
                    Label("Scout Now", systemImage: "bolt.fill")
                }
                .disabled(dataManager.isScouting)
            }
        }
    }
}
