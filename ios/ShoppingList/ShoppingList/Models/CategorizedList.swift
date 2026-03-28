import Foundation

struct CategorizedSection: Codable, Identifiable {
    var id: String { name }
    let name: String
    var items: [ShoppingItem]
}

struct CategorizedList: Codable {
    let listName: String
    let shop: String
    var sections: [CategorizedSection]

    enum CodingKeys: String, CodingKey {
        case listName = "list_name"
        case shop
        case sections
    }
}
