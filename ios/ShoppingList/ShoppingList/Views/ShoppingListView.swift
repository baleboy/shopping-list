import SwiftUI

struct ShoppingListView: View {
    let listName: String
    let shop: ShopProfile
    @State private var viewModel: ShoppingListViewModel

    init(listName: String, shop: ShopProfile, viewModel: ShoppingListViewModel? = nil) {
        self.listName = listName
        self.shop = shop
        self._viewModel = State(initialValue: viewModel ?? ShoppingListViewModel(listName: listName, shop: shop))
    }

    var body: some View {
        Group {
            if viewModel.isLoading {
                ProgressView("Preparing list...")
            } else if let error = viewModel.errorMessage {
                VStack(spacing: 16) {
                    Text(error)
                        .foregroundStyle(.secondary)
                    Button("Retry") {
                        Task { await viewModel.loadList() }
                    }
                }
            } else if let list = viewModel.categorizedList {
                List {
                    ForEach(list.sections) { section in
                        Section(section.name.capitalized) {
                            ForEach(section.items) { item in
                                Button {
                                    Task { await viewModel.toggleItem(item, inSection: section) }
                                } label: {
                                    HStack {
                                        Image(systemName: item.checked ? "checkmark.circle.fill" : "circle")
                                            .foregroundStyle(item.checked ? .green : .primary)
                                        Text(item.name)
                                            .strikethrough(item.checked)
                                            .foregroundStyle(item.checked ? .secondary : .primary)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("\(listName) (\(viewModel.itemsRemaining) left)")
        .refreshable { await viewModel.loadList(forceRefresh: true) }
        .task { await viewModel.loadList() }
    }
}

#Preview {
    let shop = ShopProfile(id: "lidl", name: "Lidl Main Street", sections: ["produce", "dairy", "bakery"])
    let viewModel = ShoppingListViewModel(listName: "master", shop: shop)
    viewModel.categorizedList = CategorizedList(
        listName: "master",
        shop: "lidl",
        sections: [
            CategorizedSection(name: "produce", items: [
                ShoppingItem(name: "bananas", checked: false),
                ShoppingItem(name: "tomatoes", checked: true),
                ShoppingItem(name: "onions", checked: false),
            ]),
            CategorizedSection(name: "dairy", items: [
                ShoppingItem(name: "milk", checked: false),
                ShoppingItem(name: "cheddar cheese", checked: false),
            ]),
            CategorizedSection(name: "bakery", items: [
                ShoppingItem(name: "sourdough bread", checked: true),
            ]),
        ]
    )
    return NavigationStack {
        ShoppingListView(listName: "master", shop: shop, viewModel: viewModel)
    }
}
