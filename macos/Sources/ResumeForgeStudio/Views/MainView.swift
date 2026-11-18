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
            } else if dataManager.selectedTab == "GITHUB" {
                GitHubRepoListView()
            } else {
                ApplicationListView()
            }
        } detail: {
            if dataManager.selectedTab == "GITHUB" {
                GitHubRepoDetailView(repo: dataManager.selectedRepo)
            } else {
                ApplicationDetailView(app: dataManager.selectedApp)
            }
        }
        .navigationSplitViewStyle(.balanced)
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button(action: {
                    Task {
                        await dataManager.fetchApplications()
                        await dataManager.fetchInboxFeed()
                        await dataManager.fetchGitHubRepos()
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

            if dataManager.selectedTab == "APPLICATIONS" {
                ToolbarItem(placement: .automatic) {
                    Button(action: {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            dataManager.showInspector.toggle()
                        }
                    }) {
                        Label("ATS Inspector", systemImage: "gauge.with.needle.fill")
                            .foregroundStyle(dataManager.showInspector ? Color.purple : Color.secondary)
                    }
                    .keyboardShortcut("i", modifiers: [.command])
                    .help("Toggle ATS Match Inspector (⌘I)")
                }
            }
        }
    }
}
