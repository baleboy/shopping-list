import Testing
import Foundation
@testable import ShoppingList

struct ShoppingListTests {

    @Test func shopProfileDecodesFromJSON() throws {
        let json = """
        {"id": "lidl", "name": "Lidl Main Street", "sections": ["produce", "dairy"]}
        """.data(using: .utf8)!
        let shop = try JSONDecoder().decode(ShopProfile.self, from: json)
        #expect(shop.id == "lidl")
        #expect(shop.name == "Lidl Main Street")
        #expect(shop.sections == ["produce", "dairy"])
    }

    @Test func shoppingItemDecodesWithCheckedState() throws {
        let json = """
        {"name": "milk", "checked": true}
        """.data(using: .utf8)!
        let item = try JSONDecoder().decode(ShoppingItem.self, from: json)
        #expect(item.name == "milk")
        #expect(item.checked == true)
    }

    @Test func categorizedListDecodesFullStructure() throws {
        let json = """
        {
            "list_name": "weekly",
            "shop": "lidl",
            "sections": [
                {
                    "name": "dairy",
                    "items": [{"name": "milk", "checked": false}]
                }
            ]
        }
        """.data(using: .utf8)!
        let list = try JSONDecoder().decode(CategorizedList.self, from: json)
        #expect(list.listName == "weekly")
        #expect(list.shop == "lidl")
        #expect(list.sections.count == 1)
        #expect(list.sections[0].items[0].name == "milk")
    }
}
