import SwiftUI

@Observable
class ShopEditorViewModel {
    var name: String
    var sections: [String]
    var newSectionName = ""
    var isSaving = false
    var errorMessage: String?

    let shopId: String

    init(shop: ShopProfile) {
        self.shopId = shop.id
        self.name = shop.name
        self.sections = shop.sections
    }

    func addSection() {
        let trimmed = newSectionName.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        sections.append(trimmed)
        newSectionName = ""
    }

    func deleteSection(at offsets: IndexSet) {
        sections.remove(atOffsets: offsets)
    }

    func moveSection(from source: IndexSet, to destination: Int) {
        sections.move(fromOffsets: source, toOffset: destination)
    }

    func save() async -> ShopProfile? {
        isSaving = true
        errorMessage = nil
        do {
            let updated = try await APIClient.shared.updateShop(id: shopId, name: name, sections: sections)
            isSaving = false
            return updated
        } catch {
            errorMessage = "Failed to save: \(error.localizedDescription)"
            isSaving = false
            return nil
        }
    }
}
