import SwiftUI

struct ContentView: View {
    @State private var selectedShop: ShopProfile?

    var body: some View {
        NavigationStack {
            ShopPickerView(selectedShop: $selectedShop)
                .navigationDestination(item: $selectedShop) { shop in
                    ListPickerView(shop: shop)
                }
        }
    }
}
