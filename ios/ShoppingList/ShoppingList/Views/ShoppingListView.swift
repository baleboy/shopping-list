import SwiftUI

struct ShoppingListView: View {
    let listName: String
    let shop: ShopProfile

    var body: some View {
        Text("Shopping: \(listName) at \(shop.name)")
            .navigationTitle(listName)
    }
}
