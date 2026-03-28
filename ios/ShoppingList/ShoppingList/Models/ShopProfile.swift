import Foundation

struct ShopProfile: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let sections: [String]
}
