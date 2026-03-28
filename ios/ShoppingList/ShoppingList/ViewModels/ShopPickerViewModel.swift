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

    func loadShops() async {
        isLoading = true
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
}
