// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ResumeForgeStudio",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "ResumeForgeStudio", targets: ["ResumeForgeStudio"])
    ],
    targets: [
        .executableTarget(
            name: "ResumeForgeStudio",
            path: "Sources/ResumeForgeStudio"
        )
    ]
)
