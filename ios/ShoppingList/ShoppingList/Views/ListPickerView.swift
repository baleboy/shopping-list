import SwiftUI

struct ListPickerView: View {
    let shop: ShopProfile
    @State private var viewModel: ListPickerViewModel
    @State private var selectedList: String?

    init(shop: ShopProfile, viewModel: ListPickerViewModel = ListPickerViewModel()) {
        self.shop = shop
        self._viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Loading lists...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadLists() }
                    }
                }
            } else {
                List(viewModel.lists, id: \.self) { listName in
                    Button(listName) {
                        selectedList = listName
                    }
                }
            }
        }
        .navigationTitle("Select List")
        .navigationDestination(item: $selectedList) { listName in
            ShoppingListView(listName: listName, shop: shop)
        }
        .task { await viewModel.loadLists() }
    }
}

#Preview {
    let viewModel = ListPickerViewModel()
    viewModel.lists = ["master", "party-supplies", "2026-03-28"]
    return NavigationStack {
        ListPickerView(
            shop: ShopProfile(id: "lidl", name: "Lidl Main Street", sections: ["produce", "dairy"]),
            viewModel: viewModel
        )
    }
}
