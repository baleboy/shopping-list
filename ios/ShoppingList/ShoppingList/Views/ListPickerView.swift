import SwiftUI

struct ListPickerView: View {
    let shop: ShopProfile

    var body: some View {
        Text("Lists for \(shop.name)")
            .navigationTitle("Select List")
    }
}
