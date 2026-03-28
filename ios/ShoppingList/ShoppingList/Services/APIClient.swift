import Foundation

class APIClient {
    static let shared = APIClient()

    private var baseURL = URL(string: "https://server-patient-frost-6137.fly.dev")!
    private var apiKey = "88e6d7665f902358ddf20e9e48cf8164b6f46267a7d80b3a3142403f0b1a87f1"

    func configure(baseURL: URL, apiKey: String) {
        self.baseURL = baseURL
        self.apiKey = apiKey
    }

    private func request(_ path: String, method: String = "GET", body: Data? = nil, query: [String: String] = [:]) async throws -> Data {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !query.isEmpty {
            components.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        var request = URLRequest(url: components.url!)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !apiKey.isEmpty {
            request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        request.httpBody = body
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) else {
            let http = response as? HTTPURLResponse
            throw APIError.httpError(statusCode: http?.statusCode ?? 0)
        }
        return data
    }

    func getShops() async throws -> [ShopProfile] {
        let data = try await request("/shops")
        return try JSONDecoder().decode([ShopProfile].self, from: data)
    }

    func getLists() async throws -> [String] {
        let data = try await request("/lists")
        return try JSONDecoder().decode([String].self, from: data)
    }

    func prepareList(name: String, shop: String) async throws -> CategorizedList {
        let data = try await request("/lists/\(name)/prepare", method: "POST", query: ["shop": shop])
        return try JSONDecoder().decode(CategorizedList.self, from: data)
    }

    func toggleItem(listName: String, item: String, shop: String) async throws {
        _ = try await request("/lists/\(listName)/items/\(item)", method: "PATCH", query: ["shop": shop])
    }
}

enum APIError: Error {
    case httpError(statusCode: Int)
}
