import SwiftUI

public struct CustomJDSheet: View {
    public let application: Application
    @Binding public var isPresented: Bool

    @ObservedObject private var dataManager = DataManager.shared
    @State private var jdText: String = ""
    @State private var selectedPreset: String? = nil

    public init(application: Application, isPresented: Binding<Bool>) {
        self.application = application
        self._isPresented = isPresented
    }

    private let presets: [(id: String, title: String, icon: String, text: String)] = [
        (
            id: "systems",
            title: "Systems & Low-Level (C++)",
            icon: "cpu.fill",
            text: "Software Engineer Intern. Requirements: C++, C, Linux systems programming, POSIX, real-time control, multithreading, concurrency, kernel/driver architecture, algorithms, performance profiling, memory management, automated unit tests, Git, CI/CD."
        ),
        (
            id: "fullstack",
            title: "Web & Fullstack",
            icon: "globe",
            text: "Fullstack Engineering Intern. Requirements: TypeScript, JavaScript, React, Next.js, Node.js, FastAPI, REST APIs, SQL, database design, offline-first PWA, CSS/Tailwind, performance optimization, web accessibility, automated testing, Git."
        ),
        (
            id: "distributed",
            title: "Backend & Distributed Systems",
            icon: "server.rack",
            text: "Backend Engineering Intern. Requirements: Python, Go, distributed systems, high-concurrency architectures, microservices, Docker, Kubernetes, Redis, PostgreSQL, gRPC, asynchronous queues, telemetry, CI/CD pipelines, system reliability."
        ),
        (
            id: "macos",
            title: "Native macOS & Swift",
            icon: "laptopcomputer",
            text: "macOS Software Engineer Intern. Requirements: Swift, SwiftUI, AppKit, Objective-C/C++, Instruments profiling, libusb, system daemons, user-space drivers, asynchronous concurrency, Apple Silicon optimization, XCTest."
        )
    ]

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("ATS Target Keywords & Job Description")
                        .font(.headline)
                        .fontWeight(.bold)
                    Text("Tailor \(application.company) (\(application.role)) with real requirements")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(.plain)
            }

            // Domain Presets
            VStack(alignment: .leading, spacing: 8) {
                Text("Instant Domain Presets:")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.secondary)

                HStack(spacing: 8) {
                    ForEach(presets, id: \.id) { p in
                        Button(action: {
                            selectedPreset = p.id
                            jdText = p.text
                        }) {
                            HStack(spacing: 5) {
                                Image(systemName: p.icon)
                                Text(p.title)
                            }
                            .font(.caption2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(selectedPreset == p.id ? Color.accentColor.opacity(0.2) : Color.secondary.opacity(0.1))
                            .foregroundStyle(selectedPreset == p.id ? Color.accentColor : Color.primary)
                            .cornerRadius(6)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

            // Text Editor
            VStack(alignment: .leading, spacing: 6) {
                Text("Paste Job Posting or Custom Requirements:")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.secondary)

                TextEditor(text: $jdText)
                    .font(.system(.body, design: .monospaced))
                    .frame(minHeight: 140)
                    .padding(8)
                    .background(Color(NSColor.controlBackgroundColor))
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
                    )
            }

            // Action Buttons
            HStack {
                Button("Cancel") {
                    isPresented = false
                }
                .keyboardShortcut(.cancelAction)

                Spacer()

                Button(action: {
                    Task {
                        await dataManager.updateJobDescription(app: application, jd: jdText)
                        isPresented = false
                    }
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "sparkles")
                        Text("⚡ Apply & Boost ATS Score")
                    }
                    .fontWeight(.semibold)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.defaultAction)
                .disabled(jdText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .padding(20)
        .frame(width: 580, height: 420)
        .onAppear {
            if let saved = application.job_description, !saved.isEmpty {
                jdText = saved
            } else if let curJD = dataManager.currentATSResult?.job_description, !curJD.isEmpty {
                jdText = curJD
            } else {
                jdText = "\(application.role) at \(application.company). Requirements: algorithms, systems architecture, distributed systems, git, automated testing, CI/CD, performance optimization, Linux, APIs."
            }
        }
    }
}
