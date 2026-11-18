import SwiftUI

public struct DeadlinePickerSheet: View {
    public let application: Application
    @Binding public var isPresented: Bool

    @State private var selectedDate: Date = Calendar.current.date(byAdding: .day, value: 7, to: Date()) ?? Date()
    @State private var isOA: Bool = false
    @State private var syncToAppleCalendar: Bool = true
    @State private var openGoogleCalendar: Bool = false
    @State private var isSaving: Bool = false

    @ObservedObject private var dataManager = DataManager.shared
    @ObservedObject private var calendarManager = CalendarManager.shared

    public init(application: Application, isPresented: Binding<Bool>) {
        self.application = application
        self._isPresented = isPresented
        if let existing = application.effectiveDeadlineDate {
            self._selectedDate = State(initialValue: existing)
        }
        self._isOA = State(initialValue: application.status == "OA_PENDING")
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            // Header
            HStack {
                Label("Set Deadline & Calendar Reminder", systemImage: "calendar.badge.clock")
                    .font(.headline)
                    .foregroundStyle(.primary)
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                        .font(.title3)
                }
                .buttonStyle(.plain)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("\(application.company) — \(application.role)")
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(application.url)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)

            Divider()

            // Date & Time Picker
            DatePicker(
                "Deadline Date & Time:",
                selection: $selectedDate,
                in: Date()...,
                displayedComponents: [.date, .hourAndMinute]
            )
            .datePickerStyle(.graphical)
            .padding(.horizontal, 4)

            // Deadline Type Picker
            Picker("Deadline Type:", selection: $isOA) {
                Text("Job Application Close").tag(false)
                Text("Online Assessment (OA)").tag(true)
            }
            .pickerStyle(.segmented)

            // Calendar Options
            VStack(alignment: .leading, spacing: 8) {
                Toggle(isOn: $syncToAppleCalendar) {
                    HStack {
                        Image(systemName: "calendar")
                            .foregroundStyle(.red)
                        Text("Sync to Apple Calendar (with 48h & 2h alerts)")
                    }
                }

                Toggle(isOn: $openGoogleCalendar) {
                    HStack {
                        Image(systemName: "globe")
                            .foregroundStyle(.blue)
                        Text("Open 1-Click Link in Google Calendar")
                    }
                }
            }
            .font(.callout)
            .padding(.top, 4)

            Spacer()

            // Action Buttons
            HStack {
                Button("Cancel") {
                    isPresented = false
                }
                .keyboardShortcut(.cancelAction)

                Spacer()

                Button(action: saveDeadline) {
                    if isSaving {
                        ProgressView().scaleEffect(0.7)
                    } else {
                        Text("Save & Sync Calendar")
                            .fontWeight(.semibold)
                    }
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.defaultAction)
                .disabled(isSaving)
            }
        }
        .padding(20)
        .frame(width: 440, height: 580)
    }

    private func saveDeadline() {
        isSaving = true
        let df = DateFormatter()
        df.dateFormat = "yyyy-MM-dd"
        let dateStr = df.string(from: selectedDate)

        Task {
            // 1. Save in SQLite / REST API
            await dataManager.setDeadline(app: application, dateString: dateStr, isOA: isOA)

            // 2. Sync to Apple Calendar
            if syncToAppleCalendar {
                _ = try? await calendarManager.addToAppleCalendar(application: application, deadlineDate: selectedDate, isOA: isOA)
            }

            // 3. Open in Google Calendar
            if openGoogleCalendar {
                calendarManager.openInGoogleCalendar(application: application, deadlineDate: selectedDate, isOA: isOA)
            }

            isSaving = false
            isPresented = false
        }
    }
}
