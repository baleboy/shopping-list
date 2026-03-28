import SwiftUI

struct ShopPickerView: View {
    @State private var viewModel = ShopPickerViewModel()
    @Binding var selectedShop: ShopProfile?

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
