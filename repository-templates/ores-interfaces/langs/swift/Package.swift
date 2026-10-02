// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "OresInterfaces",
    products: [.library(name: "OresInterfaces", targets: ["OresInterfaces"])],
    targets: [
        .target(name: "OresInterfaces"),
        .testTarget(name: "OresInterfacesTests", dependencies: ["OresInterfaces"]),
    ]
)
