import Foundation

@Observable
class ListPickerViewModel {
    var lists: [String] = []
    var isLoading = false
    var errorMessage: String?

    func loadLists() async {
        guard lists.isEmpty else { return }
        isLoading = true
        errorMessage = nil
        do {
            lists = try await APIClient.shared.getLists()
        } catch {
            errorMessage = "Failed to load lists: \(error.localizedDescription)"
        }
        isLoading = false
    }
}
