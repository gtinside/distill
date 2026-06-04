import Foundation
import Supabase

// SUPABASE_URL and SUPABASE_ANON_KEY are injected via Secrets.xcconfig (gitignored).
// See Secrets.xcconfig.example for the required format.
private let supabaseURL: URL = {
    guard let raw = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_URL") as? String,
          let url = URL(string: raw) else {
        fatalError("SUPABASE_URL missing from Info.plist — check Secrets.xcconfig")
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
