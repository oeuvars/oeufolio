// Lifts the subject out of a photograph with macOS Vision and writes its mask as a greyscale PNG, for cats.py:
//     xcrun swift studio/signal/mask.swift photo.jpg mask.png
import AppKit
import CoreImage
import Vision

let args = CommandLine.arguments
let input = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])
let handler = VNImageRequestHandler(url: input)
let request = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([request])
guard let result = request.results?.first else { print("no subject"); exit(1) }
print("instances", result.allInstances.count)
let buffer = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
let image = CIImage(cvPixelBuffer: buffer)
let context = CIContext()
let cg = context.createCGImage(image, from: image.extent)!
let rep = NSBitmapImageRep(cgImage: cg)
try rep.representation(using: .png, properties: [:])!.write(to: output)
