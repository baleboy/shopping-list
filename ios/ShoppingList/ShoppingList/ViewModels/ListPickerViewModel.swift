import Foundation

@Observable
class ListPickerViewModel {
    var lists: [String] = []
    var isLoading = false
    var errorMessage: String?

    func loadLists() async {
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
