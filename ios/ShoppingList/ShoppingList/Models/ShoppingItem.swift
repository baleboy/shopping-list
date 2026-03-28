import Foundation

struct ShoppingItem: Codable, Identifiable {
    var id: String { name }
    let name: String
    var checked: Bool
}
