import SwiftUI

struct ShopPickerView: View {
    @State private var viewModel: ShopPickerViewModel
    @Binding var selectedShop: ShopProfile?

    init(selectedShop: Binding<ShopProfile?>, viewModel: ShopPickerViewModel = ShopPickerViewModel()) {
        self._selectedShop = selectedShop
        self._viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading shops...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadShops() }
                    }
                }
            } else {
                List(viewModel.shops) { shop in
                    Button {
                        viewModel.selectShop(shop)
                        selectedShop = shop
                    } label: {
                        HStack {
                            Text(shop.name)
                            Spacer()
                            if shop.id == viewModel.lastSelectedShopId {
                                Image(systemName: "clock")
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Select Shop")
        .task { await viewModel.loadShops() }
    }
}

#Preview {
    let viewModel = ShopPickerViewModel()
    viewModel.shops = [
        ShopProfile(id: "lidl", name: "Lidl Main Street", sections: ["produce", "dairy", "bakery"]),
        ShopProfile(id: "tesco", name: "Tesco Express", sections: ["fruit & veg", "dairy", "meat"]),
    ]
    return NavigationStack {
        ShopPickerView(selectedShop: .constant(nil), viewModel: viewModel)
    }
}
