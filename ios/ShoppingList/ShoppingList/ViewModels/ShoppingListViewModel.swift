import Foundation

@Observable
class ShoppingListViewModel {
    var categorizedList: CategorizedList?
    var isLoading = false
    var errorMessage: String?

    let listName: String
    let shop: ShopProfile

    init(listName: String, shop: ShopProfile) {
        self.listName = listName
        self.shop = shop
    }

    var itemsRemaining: Int {
        guard let list = categorizedList else { return 0 }
        return list.sections.flatMap(\.items).filter { !$0.checked }.count
    }

    func loadList() async {
        isLoading = true
        errorMessage = nil
        do {
            categorizedList = try await APIClient.shared.prepareList(name: listName, shop: shop.id)
        } catch {
            errorMessage = "Failed to load list: \(error.localizedDescription)"
        }
        isLoading = false
    }

    func toggleItem(_ item: ShoppingItem, inSection section: CategorizedSection) async {
        guard var list = categorizedList,
              let sectionIndex = list.sections.firstIndex(where: { $0.id == section.id }),
              let itemIndex = list.sections[sectionIndex].items.firstIndex(where: { $0.id == item.id }) else {
            return
        }

        // Optimistic update
        list.sections[sectionIndex].items[itemIndex].checked.toggle()
        categorizedList = list

        do {
            try await APIClient.shared.toggleItem(listName: listName, item: item.name, shop: shop.id)
        } catch {
            // Revert on failure
            list.sections[sectionIndex].items[itemIndex].checked.toggle()
            categorizedList = list
        }
    }
}
