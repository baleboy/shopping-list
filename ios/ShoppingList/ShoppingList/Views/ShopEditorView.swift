import SwiftUI

struct ShopEditorView: View {
    @State private var viewModel: ShopEditorViewModel
    @Environment(\.dismiss) private var dismiss
    var onSave: (() -> Void)?

    init(shop: ShopProfile, onSave: (() -> Void)? = nil) {
        self._viewModel = State(initialValue: ShopEditorViewModel(shop: shop))
        self.onSave = onSave
    }

    var body: some View {
        Form {
            Section("Shop Name") {
                TextField("Name", text: $viewModel.name)
            }

            Section("Sections (drag to reorder)") {
                List {
                    ForEach(viewModel.sections, id: \.self) { section in
                        Text(section)
                    }
                    .onMove { viewModel.moveSection(from: $0, to: $1) }
                    .onDelete { viewModel.deleteSection(at: $0) }
                }

                HStack {
                    TextField("New section", text: $viewModel.newSectionName)
                    Button("Add") {
                        viewModel.addSection()
                    }
                    .disabled(viewModel.newSectionName.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }

            if let error = viewModel.errorMessage {
                Section {
                    Text(error)
                        .foregroundStyle(.red)
                }
            }
        }
        .navigationTitle("Edit Shop")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Save") {
                    Task {
                        if await viewModel.save() != nil {
                            onSave?()
                            dismiss()
                        }
                    }
                }
                .disabled(viewModel.name.trimmingCharacters(in: .whitespaces).isEmpty || viewModel.isSaving)
            }
        }
        .environment(\.editMode, .constant(.active))
    }
}

#Preview {
    NavigationStack {
        ShopEditorView(shop: ShopProfile(
            id: "lidl",
            name: "Lidl Main Street",
            sections: ["produce", "dairy", "bakery", "frozen"]
        ))
    }
}
