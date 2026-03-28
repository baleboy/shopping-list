import Foundation

struct ShopProfile: Codable, Identifiable {
    let id: String
    let name: String
    let sections: [String]
}
