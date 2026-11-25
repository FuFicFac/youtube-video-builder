import Foundation
import AVFoundation
import Vision
import CoreVideo

// Usage: person-mask source.mp4 start_seconds duration_seconds mask.gray [accurate|balanced]
// Frame rate: PERSON_MASK_FPS="30000/1000" (rational num/den; default 24000/1001). Match the measured source FPS.
// Build once: swiftc -O person-mask.swift -o person-mask   (macOS, Apple Vision)
let args = CommandLine.arguments
if args.count < 5 {
    fputs("Usage: person-mask source.mp4 start duration output.gray [accurate|balanced]\n", stderr)
    exit(2)
}
let source = URL(fileURLWithPath: args[1])
let start = Double(args[2])!
let duration = Double(args[3])!
let outputURL = URL(fileURLWithPath: args[4])
let asset = AVURLAsset(url: source)
guard let track = asset.tracks(withMediaType: .video).first else { fatalError("No video track") }
let reader = try AVAssetReader(asset: asset)
// Align to the same next real source frame selected by ffmpeg's accurate -ss.
// AVAssetReader otherwise emits a clipped partial sample before that frame.
let fpsParts = (ProcessInfo.processInfo.environment["PERSON_MASK_FPS"] ?? "24000/1001").split(separator: "/").map { Int64($0)! }
let fpsNum = fpsParts[0], fpsDen = fpsParts.count > 1 ? fpsParts[1] : 1
let fps = Double(fpsNum) / Double(fpsDen)
let firstFrame = Int64(ceil(start * fps - 0.000001))
let frameCount = Int64((duration * fps).rounded())
reader.timeRange = CMTimeRange(start: CMTime(value:firstFrame * fpsDen, timescale:Int32(fpsNum)), duration:CMTime(value:frameCount * fpsDen, timescale:Int32(fpsNum)))
let output = AVAssetReaderTrackOutput(track:track, outputSettings:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA])
output.alwaysCopiesSampleData = false
reader.add(output)
let request = VNGeneratePersonSegmentationRequest()
request.usesCPUOnly = ProcessInfo.processInfo.environment["PERSON_MASK_CPU_ONLY"] == "1"
request.qualityLevel = (args.count > 5 && args[5] == "balanced") ? .balanced : .accurate
request.outputPixelFormat = kCVPixelFormatType_OneComponent8
FileManager.default.createFile(atPath:outputURL.path, contents:nil)
let handle = try FileHandle(forWritingTo:outputURL)
let clock = Date()
var count = 0
var width = 0
var height = 0
var firstPTS = 0.0
var lastPTS = 0.0
reader.startReading()
while let sample = output.copyNextSampleBuffer() {
    try autoreleasepool {
        guard let image = CMSampleBufferGetImageBuffer(sample) else { return }
        let handler = VNImageRequestHandler(cvPixelBuffer:image, orientation:.up, options:[:])
        try handler.perform([request])
        guard let mask = request.results?.first?.pixelBuffer else { throw NSError(domain:"PersonMask",code:1) }
        CVPixelBufferLockBaseAddress(mask,.readOnly)
        defer { CVPixelBufferUnlockBaseAddress(mask,.readOnly) }
        width = CVPixelBufferGetWidth(mask)
        height = CVPixelBufferGetHeight(mask)
        let stride = CVPixelBufferGetBytesPerRow(mask)
        let base = CVPixelBufferGetBaseAddress(mask)!
        if width == stride { try handle.write(contentsOf:Data(bytes:base,count:width*height)) }
        else { for y in 0..<height { try handle.write(contentsOf:Data(bytes:base.advanced(by:y*stride),count:width)) } }
        let pts = CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sample))
        if count == 0 { firstPTS = pts }
        lastPTS = pts
        count += 1
    }
}
try handle.close()
if reader.status == .failed { fatalError("Reader failed: \(String(describing:reader.error))") }
let metadata:[String:Any] = ["source":source.path,"start_requested":start,"duration_requested":duration,"first_pts":firstPTS,"last_pts":lastPTS,"frames":count,"mask_width":width,"mask_height":height,"elapsed_seconds":Date().timeIntervalSince(clock),"quality":args.count > 5 ? args[5] : "accurate"]
let json = try JSONSerialization.data(withJSONObject:metadata, options:[.prettyPrinted,.sortedKeys])
try json.write(to:URL(fileURLWithPath:args[4]+".json"))
fputs(String(data:json,encoding:.utf8)!+"\n",stderr)
