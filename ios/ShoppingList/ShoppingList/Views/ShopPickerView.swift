import SwiftUI

struct ShopPickerView: View {
    @State private var viewModel: ShopPickerViewModel
    @Binding var selectedShop: ShopProfile?
    @State private var showingAddAlert = false
    @State private var newShopName = ""
    @State private var shopToEdit: ShopProfile?
    @State private var showingDeleteConfirm = false
    @State private var shopToDelete: ShopProfile?

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
                        Task { await viewModel.loadShops(forceRefresh: true) }
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
                    .swipeActions(edge: .trailing) {
                        Button(role: .destructive) {
                            shopToDelete = shop
                            showingDeleteConfirm = true
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                        Button {
                            shopToEdit = shop
                        } label: {
                            Label("Edit", systemImage: "pencil")
                        }
                        .tint(.blue)
                    }
                }
            }
        }
        .navigationTitle("Select Shop")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    newShopName = ""
                    showingAddAlert = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .alert("New Shop", isPresented: $showingAddAlert) {
            TextField("Shop name", text: $newShopName)
            Button("Cancel", role: .cancel) {}
            Button("Add") {
                Task { await viewModel.createShop(name: newShopName) }
            }
        }
        .alert("Delete Shop?", isPresented: $showingDeleteConfirm) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                if let shop = shopToDelete {
                    Task { await viewModel.deleteShop(shop) }
                }
            }
        } message: {
            if let shop = shopToDelete {
                Text("Delete \"\(shop.name)\"? This cannot be undone.")
            }
        }
        .navigationDestination(item: $shopToEdit) { shop in
            ShopEditorView(shop: shop) {
                Task { await viewModel.loadShops(forceRefresh: true) }
            }
        }
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
