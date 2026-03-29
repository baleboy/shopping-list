import Foundation

@Observable
class ShopPickerViewModel {
    var shops: [ShopProfile] = []
    var isLoading = false
    var errorMessage: String?

    private let lastShopKey = "lastSelectedShop"

    var lastSelectedShopId: String? {
        get { UserDefaults.standard.string(forKey: lastShopKey) }
        set { UserDefaults.standard.set(newValue, forKey: lastShopKey) }
    }

    func loadShops(forceRefresh: Bool = false) async {
        guard forceRefresh || shops.isEmpty else { return }
        isLoading = shops.isEmpty
        errorMessage = nil
        do {
            shops = try await APIClient.shared.getShops()
        } catch {
            errorMessage = "Failed to load shops: \(error.localizedDescription)"
        }
        isLoading = false
    }

    func selectShop(_ shop: ShopProfile) {
        lastSelectedShopId = shop.id
    }

    func createShop(name: String) async -> ShopProfile? {
        do {
            let shop = try await APIClient.shared.createShop(name: name)
            await loadShops(forceRefresh: true)
            return shop
        } catch {
            errorMessage = "Failed to create shop: \(error.localizedDescription)"
            return nil
        }
    }

    func deleteShop(_ shop: ShopProfile) async {
        do {
            try await APIClient.shared.deleteShop(id: shop.id)
            await loadShops(forceRefresh: true)
        } catch {
            errorMessage = "Failed to delete shop: \(error.localizedDescription)"
        }
    }
}
