import SwiftUI

struct ShoppingListView: View {
    let listName: String
    let shop: ShopProfile
    @State private var viewModel: ShoppingListViewModel
    @AppStorage("hidePurchased") private var hidePurchased = false
    @State private var isReorderingSections = false

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
                if isReorderingSections {
                    List {
                        ForEach(list.sections) { section in
                            HStack {
                                Image(systemName: "line.3.horizontal")
                                    .foregroundStyle(.secondary)
                                Text(section.name.capitalized)
                                Spacer()
                                Text("\(section.items.count)")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .onMove { source, destination in
                            viewModel.moveSections(from: source, to: destination)
                        }
                    }
                    .environment(\.editMode, .constant(.active))
                } else {
                    List {
                        ForEach(list.sections) { section in
                            let visibleItems = hidePurchased ? section.items.filter { !$0.checked } : section.items
                            if !visibleItems.isEmpty {
                                Section(section.name.capitalized) {
                                    ForEach(visibleItems) { item in
                                        HStack {
                                            Image(systemName: item.checked ? "checkmark.circle.fill" : "circle")
                                                .foregroundStyle(item.checked ? .green : .primary)
                                            Text(item.name)
                                                .strikethrough(item.checked)
                                                .foregroundStyle(item.checked ? .secondary : .primary)
                                        }
                                        .contentShape(Rectangle())
                                        .onTapGesture {
                                            Task { await viewModel.toggleItem(item, inSection: section) }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("\(listName) (\(viewModel.itemsRemaining) left)")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Toggle(isOn: $hidePurchased) {
                    Image(systemName: hidePurchased ? "eye.slash" : "eye")
                }
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    viewModel.resetAllItems()
                } label: {
                    Image(systemName: "arrow.counterclockwise")
                }
                .disabled(viewModel.itemsRemaining == (viewModel.categorizedList?.sections.flatMap(\.items).count ?? 0))
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    isReorderingSections.toggle()
                } label: {
                    Image(systemName: isReorderingSections ? "checkmark" : "arrow.up.arrow.down")
                }
                .disabled(viewModel.categorizedList == nil)
            }
        }
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
