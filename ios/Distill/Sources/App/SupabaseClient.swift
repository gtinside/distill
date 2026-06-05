import Foundation
import Supabase

// SUPABASE_HOST and SUPABASE_ANON_KEY are injected via Secrets.xcconfig (gitignored).
// URL protocol is prepended here to avoid xcconfig treating // as a comment.
private let supabaseURL: URL = {
    guard let host = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_HOST") as? String,
          !host.isEmpty,
          let url = URL(string: "https://\(host)") else {
        fatalError("SUPABASE_HOST missing from Info.plist — check Secrets.xcconfig")
    }
    return url
}()

private let supabaseAnonKey: String = {
    guard let key = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_ANON_KEY") as? String,
          !key.isEmpty else {
        fatalError("SUPABASE_ANON_KEY missing from Info.plist — check Secrets.xcconfig")
    }
    return key
}()

let supabase = SupabaseClient(supabaseURL: supabaseURL, supabaseKey: supabaseAnonKey)
