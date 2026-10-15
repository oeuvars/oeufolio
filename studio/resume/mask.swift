// Lifts each subject out of a photograph with macOS Vision and writes each one's mask as a greyscale PNG, for cats.py
// to keep the cat's and leave a lamp or a cushion beside it behind:
//     xcrun swift studio/resume/mask.swift photo.jpg out
// writes out-0.png, out-1.png and so on.
import AppKit
import CoreImage
import Vision

let args = CommandLine.arguments
let handler = VNImageRequestHandler(url: URL(fileURLWithPath: args[1]))
let request = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([request])
guard let result = request.results?.first else { print("no subject"); exit(1) }
let context = CIContext()
for instance in result.allInstances {
    let buffer = try result.generateScaledMaskForImage(forInstances: IndexSet(integer: instance), from: handler)
    let cg = context.createCGImage(CIImage(cvPixelBuffer: buffer), from: CIImage(cvPixelBuffer: buffer).extent)!
    try NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: "\(args[2])-\(instance).png"))
    print("instance", instance)
}
