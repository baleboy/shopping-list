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

    private var cacheURL: URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return docs.appendingPathComponent("cache_\(listName)_\(shop.id).json")
    }

    private func saveToCache(_ list: CategorizedList) {
        if let data = try? JSONEncoder().encode(list) {
            try? data.write(to: cacheURL)
        }
    }

    private func loadFromCache() -> CategorizedList? {
        guard let data = try? Data(contentsOf: cacheURL) else { return nil }
        return try? JSONDecoder().decode(CategorizedList.self, from: data)
    }

    func loadList() async {
        guard categorizedList == nil else { return }
        isLoading = true
        errorMessage = nil
        do {
            let list = try await APIClient.shared.prepareList(name: listName, shop: shop.id)
            categorizedList = list
            saveToCache(list)
        } catch {
            if categorizedList == nil {
                categorizedList = loadFromCache()
            }
            if categorizedList == nil {
                errorMessage = "Failed to load list: \(error.localizedDescription)"
            }
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
        saveToCache(list)

        do {
            try await APIClient.shared.toggleItem(listName: listName, item: item.name, shop: shop.id)
        } catch {
            // Revert on failure
            list.sections[sectionIndex].items[itemIndex].checked.toggle()
            categorizedList = list
        }
    }
}
