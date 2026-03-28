import SwiftUI

struct ListPickerView: View {
    let shop: ShopProfile
    @State private var viewModel = ListPickerViewModel()
    @State private var selectedList: String?

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
