import Foundation

class APIClient {
    static let shared = APIClient()

    private var baseURL = URL(string: AppConfig.apiBaseURL)!
    private var apiKey = AppConfig.apiKey

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

    func createShop(name: String) async throws -> ShopProfile {
        let body = try JSONEncoder().encode(["name": name])
        let data = try await request("/shops", method: "POST", body: body)
        return try JSONDecoder().decode(ShopProfile.self, from: data)
    }

    func updateShop(id: String, name: String, sections: [String]) async throws -> ShopProfile {
        let payload: [String: Any] = ["name": name, "sections": sections]
        let body = try JSONSerialization.data(withJSONObject: payload)
        let data = try await request("/shops/\(id)", method: "PUT", body: body)
        return try JSONDecoder().decode(ShopProfile.self, from: data)
    }

    func deleteShop(id: String) async throws {
        _ = try await request("/shops/\(id)", method: "DELETE")
    }
}

enum APIError: Error {
    case httpError(statusCode: Int)
}
