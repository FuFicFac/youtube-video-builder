import Foundation
import Vision
import AppKit
// usage: facetrack <dir of jpgs> -> prints "name cx cy w h" (normalized, origin top-left) per image, largest face
let dir = CommandLine.arguments[1]
let files = try! FileManager.default.contentsOfDirectory(atPath: dir).filter { $0.hasSuffix(".jpg") }.sorted()
for f in files {
    let url = URL(fileURLWithPath: dir).appendingPathComponent(f)
    let req = VNDetectFaceRectanglesRequest()
    let h = VNImageRequestHandler(url: url, options: [:])
    try? h.perform([req])
    if let faces = req.results, let b = faces.max(by: { $0.boundingBox.width < $1.boundingBox.width })?.boundingBox {
        print(f, b.midX, 1 - b.midY, b.width, b.height)
    } else { print(f, "none") }
}
