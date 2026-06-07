import SwiftUI

struct TopicsView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = TopicsViewModel()
    @State private var showAddSheet = false
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.topics.isEmpty {
                    ProgressView()
                } else if viewModel.topics.isEmpty {
                    ContentUnavailableView(
                        "No Topics Yet",
                        systemImage: "list.bullet",
                        description: Text("Add topics to start receiving digests.")
                    )
                } else {
                    List {
                        ForEach(viewModel.topics) { topic in
                            Text(topic.phrase)
                        }
                        .onDelete { offsets in
                            Task { await viewModel.delete(at: offsets) }
                        }
                        .onMove { source, destination in
                            Task { await viewModel.move(from: source, to: destination) }
                        }
                    }
                    .listStyle(.insetGrouped)
                }
            }
            .navigationTitle("Topics")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    if !viewModel.topics.isEmpty {
                        EditButton()
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showSettings = true } label: {
                        Image(systemName: "gearshape")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showAddSheet = true } label: {
                        Image(systemName: "plus")
                    }
                    .disabled(!viewModel.canAddTopic)
                }
            }
        }
        .sheet(isPresented: $showAddSheet) {
            AddTopicSheet(viewModel: viewModel)
        }
        .sheet(isPresented: $showSettings) {
            SettingsSheet(viewModel: viewModel)
                .environmentObject(authManager)
        }
        .task {
            guard let token = try? await supabase.auth.session.accessToken else { return }
            await viewModel.load(token: token)
        }
        .alert("Error", isPresented: Binding(
            get: { viewModel.error != nil },
            set: { if !$0 { Task { @MainActor in viewModel.error = nil } } }
        )) {
            Button("OK") { }
        } message: {
            Text(viewModel.error?.localizedDescription ?? "")
        }
    }
}
