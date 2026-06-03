import SafariServices
import SwiftUI

struct DigestView: View {
    @StateObject private var viewModel = DigestViewModel()
    @State private var safariURL: URL?
    @State private var refreshingCardIds: Set<UUID> = []

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.digest == nil {
                    ProgressView()
                } else if let digest = viewModel.digest, !digest.topic_cards.isEmpty {
                    List {
                        if let cacheDate = viewModel.cacheDate {
                            Text("Offline — last updated \(cacheDate.formatted(.relative(presentation: .named)))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .frame(maxWidth: .infinity, alignment: .center)
                                .listRowSeparator(.hidden)
                                .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                        }
                        ForEach(digest.topic_cards) { card in
                            TopicCardView(
                                card: card,
                                isRefreshing: refreshingCardIds.contains(card.id),
                                onSourceTap: { url in
                                    safariURL = url
                                },
                                onRefresh: {
                                    try await handleCardRefresh(card: card)
                                }
                            )
                            .listRowSeparator(.hidden)
                            .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                        }
                    }
                    .listStyle(.plain)
                    .refreshable { await viewModel.fetch() }
                } else {
                    ContentUnavailableView(
                        "Your digest is on its way",
                        systemImage: "clock",
                        description: Text("Check back after your scheduled delivery time.")
                    )
                    .refreshable { await viewModel.fetch() }
                }
            }
            .navigationTitle("Digest")
            .alert("Error", isPresented: Binding(
                get: { viewModel.error != nil },
                set: { if !$0 { viewModel.error = nil } }
            )) {
                Button("OK") { viewModel.error = nil }
            } message: {
                Text(viewModel.error?.localizedDescription ?? "")
            }
        }
        .sheet(item: $safariURL) { url in
            SafariView(url: url)
                .ignoresSafeArea()
        }
        .task {
            guard let token = try? await supabase.auth.session.accessToken else { return }
            await viewModel.load(token: token)
        }
    }

    private func handleCardRefresh(card: TopicCard) async throws {
        guard !refreshingCardIds.contains(card.id) else { return }
        refreshingCardIds.insert(card.id)
        defer { refreshingCardIds.remove(card.id) }
        let refreshed = try await viewModel.refreshCard(topicId: card.topic_id)
        viewModel.updateCard(refreshed)
    }
}

struct TopicCardView: View {
    let card: TopicCard
    let isRefreshing: Bool
    let onSourceTap: (URL) -> Void
    let onRefresh: () async throws -> Void

    @State private var rateLimitMessage: String? = nil

    var body: some View {
        Group {
            if card.status == "error" {
                errorContent
            } else {
                normalContent
            }
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Error state

    @ViewBuilder
    private var errorContent: some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.title2)
                .foregroundStyle(.secondary)
            Text("Couldn't load this topic")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if let message = rateLimitMessage {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else if isRefreshing {
                ProgressView()
            } else {
                Button("Try again") { triggerRefresh() }
                    .buttonStyle(.bordered)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
    }

    // MARK: - Normal state

    @ViewBuilder
    private var normalContent: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                if let tldr = card.tldr {
                    Text(tldr)
                        .font(.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)
                } else {
                    Spacer()
                }
                refreshControl
            }
            if let bullets = card.bullets {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(bullets, id: \.self) { bullet in
                        HStack(alignment: .top, spacing: 8) {
                            Text("•").foregroundStyle(.secondary)
                            Text(bullet).font(.subheadline)
                        }
                    }
                }
            }
            if let message = rateLimitMessage {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            if let sources = card.sources, !sources.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(sources) { source in
                            if let url = URL(string: source.url) {
                                Button(source.title) { onSourceTap(url) }
                                    .buttonStyle(.bordered)
                                    .tint(.accentColor)
                                    .font(.caption)
                            }
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var refreshControl: some View {
        if isRefreshing {
            ProgressView().padding(.leading, 8)
        } else {
            Button { triggerRefresh() } label: {
                Image(systemName: "arrow.clockwise")
            }
            .buttonStyle(.bordered)
            .disabled(rateLimitMessage != nil)
            .padding(.leading, 8)
        }
    }

    private func triggerRefresh() {
        Task {
            do {
                try await onRefresh()
            } catch APIClient.APIError.rateLimited(let message) {
                rateLimitMessage = message
                // Auto-clear after 4 seconds for normal cards; persist for error cards
                // (error cards that are rate-limited stay disabled until user retries later)
                if card.status != "error" {
                    try? await Task.sleep(nanoseconds: 4_000_000_000)
                    rateLimitMessage = nil
                }
            } catch {
                // Other errors surfaced via DigestView's alert
            }
        }
    }
}

// MARK: - Safari wrapper

struct SafariView: UIViewControllerRepresentable {
    let url: URL
    func makeUIViewController(context: Context) -> SFSafariViewController {
        SFSafariViewController(url: url)
    }
    func updateUIViewController(_ uiViewController: SFSafariViewController, context: Context) {}
}

extension URL: @retroactive Identifiable {
    public var id: String { absoluteString }
}
