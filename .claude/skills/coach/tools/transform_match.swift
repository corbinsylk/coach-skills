// transform_match: the before and after progress photos made as alike as possible WITHOUT touching the physique.
// The body is the locked value. Only the lighting (exposure), the skin colour, the clarity and ONE uniform scale change: no warp, no liquify,
// no AI on the body. macOS only (Apple's Vision subject lift and body pose, Core Image for the filters).
//
// usage: transform_match <before> <after> <out dir>
// writes <out dir>/before.png and after.png (both cut out on one 1440 x 2560 canvas, torso on torso) and match.json (scales, colour moves,
// and the callout points on the after's body in 1080 x 1920 reel pixels).
//
//  1. crop the black bars a phone screenshot leaves
//  2. cut-out: the subject lift mask (the Photos "lift subject" mask), eroded a touch and feathered so no room colour fringes the edge
//  3. scale: the before is scaled so its torso (neck joint to root joint) is exactly as long as the after's, so the bones match and the soft
//     tissue shows its real change; both are centred on the waist (a turned shoulder or a raised phone arm moves the neck, the waist does not)
//  4. colour: the before's skin (a torso band) takes the after's mean lightness (exposure) and its skin colour; its lightness SPREAD stays its
//     own: a full transfer raises the spread and draws shadows on the stomach that were not there
//  5. clarity: a light denoise on the before, the same gentle S curve and sharpen on both, a fine fixed grain on a lifted before (breaks the bands)
import Foundation
import Vision
import CoreImage
import CoreImage.CIFilterBuiltins

let args = CommandLine.arguments
guard args.count >= 4 else { print("usage: transform_match <before> <after> <out dir>"); exit(2) }
guard #available(macOS 14.0, *) else { print("MAC TOO OLD: the cut-out needs macOS 14 (Sonoma) or newer."); exit(3) }

let sRGB = CGColorSpace(name: CGColorSpace.sRGB)!
let gray = CGColorSpaceCreateDeviceGray()
let ctx = CIContext(options: [.workingColorSpace: sRGB, .outputColorSpace: sRGB])   // filters work in the photo's own (gamma) space
let CW = 1440, CH = 2560
let TORSO_CANVAS = 840.0              // the after's torso on the canvas: head near the top, knees off the bottom
let TARGET = (x: 720.0, y: 1520.0)    // the torso centre on the canvas
let outDir = URL(fileURLWithPath: args[3])

func fail(_ s: String) -> Never { print(s); exit(1) }

struct Photo {
  var ci: CIImage; var w: Int; var h: Int
  var mask: [UInt8] = []; var joints: [String: (Double, Double)] = [:]
  var crop: [Int] = []
}

func rgba(_ ci: CIImage) -> [UInt8] {
  let w = Int(ci.extent.width), h = Int(ci.extent.height)
  var buf = [UInt8](repeating: 0, count: w * h * 4)
  ctx.render(ci, toBitmap: &buf, rowBytes: w * 4, bounds: ci.extent, format: .RGBA8, colorSpace: sRGB)
  return buf
}
func image(_ buf: [UInt8], _ w: Int, _ h: Int) -> CIImage {
  CIImage(bitmapData: Data(buf), bytesPerRow: w * 4, size: CGSize(width: w, height: h), format: .RGBA8, colorSpace: sRGB)
}
func grayBuf(_ ci: CIImage) -> [UInt8] {
  let w = Int(ci.extent.width), h = Int(ci.extent.height)
  var buf = [UInt8](repeating: 0, count: w * h)
  ctx.render(ci, toBitmap: &buf, rowBytes: w, bounds: ci.extent, format: .L8, colorSpace: gray)
  return buf
}
func grayImage(_ buf: [UInt8], _ w: Int, _ h: Int) -> CIImage {
  CIImage(bitmapData: Data(buf), bytesPerRow: w, size: CGSize(width: w, height: h), format: .L8, colorSpace: gray)
}

func load(_ path: String, _ label: String) -> Photo {
  guard let raw = CIImage(contentsOf: URL(fileURLWithPath: path), options: [.applyOrientationProperty: true]) else {
    fail("CAN'T OPEN: the \(label) photo (\(path)). Use a JPG, PNG or HEIC.")
  }
  var ci = raw.transformed(by: CGAffineTransform(translationX: -raw.extent.minX, y: -raw.extent.minY))
  let W = Int(ci.extent.width), H = Int(ci.extent.height)
  // 1. the black bars of a phone screenshot (rows and columns whose mean is under 6 of 255)
  let b = rgba(ci)
  var rows = [Int](), cols = [Int]()
  var colSum = [Double](repeating: 0, count: W)
  for y in 0..<H {
    var s = 0.0
    for x in 0..<W { let i = (y * W + x) * 4; let v = Double(b[i]) + Double(b[i + 1]) + Double(b[i + 2]); s += v; colSum[x] += v }
    if s / Double(W * 3) > 6 { rows.append(y) }
  }
  for x in 0..<W where colSum[x] / Double(H * 3) > 6 { cols.append(x) }
  guard let r0 = rows.first, let r1 = rows.last, let c0 = cols.first, let c1 = cols.last else { fail("EMPTY PHOTO: the \(label) photo is all black.") }
  let cw = c1 - c0 + 1, chh = r1 - r0 + 1
  // Core Image counts y from the bottom
  ci = ci.cropped(to: CGRect(x: c0, y: H - 1 - r1, width: cw, height: chh))
    .transformed(by: CGAffineTransform(translationX: -CGFloat(c0), y: -CGFloat(H - 1 - r1)))
  var p = Photo(ci: ci, w: cw, h: chh); p.crop = [c0, r0, cw, chh]
  // 2. the subject lift mask and the body pose joints (image pixels, origin top-left). The photo's pixels are never changed here.
  let handler = VNImageRequestHandler(ciImage: ci)
  let fg = VNGenerateForegroundInstanceMaskRequest(), pose = VNDetectHumanBodyPoseRequest()
  do { try handler.perform([fg, pose]) } catch { fail("CUT-OUT FAILED on the \(label) photo: \(error.localizedDescription)") }
  guard let r = fg.results?.first, let mb = try? r.generateScaledMaskForImage(forInstances: r.allInstances, from: handler) else {
    fail("NO PERSON FOUND in the \(label) photo. Use a photo where the client stands clear of the background.")
  }
  p.mask = grayBuf(CIImage(cvPixelBuffer: mb))
  if let obs = pose.results?.first, let pts = try? obs.recognizedPoints(.all) {
    for (k, v) in pts where v.confidence > 0.1 { p.joints[k.rawValue.rawValue] = (Double(v.location.x) * Double(cw), (1 - Double(v.location.y)) * Double(chh)) }
  }
  if p.joints["root"] == nil, let l = p.joints["left_upLeg_joint"], let rr = p.joints["right_upLeg_joint"] { p.joints["root"] = ((l.0 + rr.0) / 2, (l.1 + rr.1) / 2) }
  for k in ["neck_1_joint", "root", "left_shoulder_1_joint", "right_shoulder_1_joint"] where p.joints[k] == nil {
    fail("BODY NOT FOUND in the \(label) photo (no \(k)). Use a front-on photo with the shoulders and hips in view.")
  }
  return p
}

func J(_ p: Photo, _ k: String) -> (Double, Double) { p.joints[k]! }
func J(_ p: Photo, _ k: String, default d: (Double, Double)) -> (Double, Double) { p.joints[k] ?? d }
func torso(_ p: Photo) -> Double { let a = J(p, "neck_1_joint"), b = J(p, "root"); return hypot(a.0 - b.0, a.1 - b.1) }
// the waist's run of mask pixels a quarter-torso above the root joint: its middle is the body's centre, its right end the waist callout
func waist(_ p: Photo) -> (l: Double, r: Double, y: Double) {
  let root = J(p, "root"); let y = max(0, min(p.h - 1, Int(root.1 - 0.2 * torso(p)))); var x = max(0, min(p.w - 1, Int(root.0)))
  if p.mask[y * p.w + x] <= 128 {   // the root can sit just outside a narrow waist: walk to the nearest body pixel
    var best = -1
    for d in 0..<p.w / 3 { for xx in [x - d, x + d] where xx >= 0 && xx < p.w && p.mask[y * p.w + xx] > 128 { best = xx; break }; if best >= 0 { break } }
    if best < 0 { return (root.0 - 50, root.0 + 50, Double(y)) }
    x = best
  }
  var l = x, r = x
  while l > 0 && p.mask[y * p.w + l - 1] > 128 { l -= 1 }
  while r < p.w - 1 && p.mask[y * p.w + r + 1] > 128 { r += 1 }
  return (Double(l), Double(r), Double(y))
}

var before = load(args[1], "before"), after = load(args[2], "after")

// ---- Lab (sRGB, D65), so the colour move is on lightness and skin colour separately
var lin = [Double](repeating: 0, count: 256)
for i in 0..<256 { let c = Double(i) / 255; lin[i] = c <= 0.04045 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4) }
@inline(__always) func fLab(_ t: Double) -> Double { t > 0.008856 ? cbrt(t) : (7.787 * t + 16.0 / 116) }
@inline(__always) func toLab(_ r: UInt8, _ g: UInt8, _ b: UInt8) -> (Double, Double, Double) {
  let R = lin[Int(r)], G = lin[Int(g)], B = lin[Int(b)]
  let X = (0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.95047, Y = 0.2126 * R + 0.7152 * G + 0.0722 * B, Z = (0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.08883
  let fx = fLab(X), fy = fLab(Y), fz = fLab(Z)
  return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
}
@inline(__always) func fromLab(_ L: Double, _ a: Double, _ b: Double) -> (Double, Double, Double) {
  let fy = (L + 16) / 116, fx = fy + a / 500, fz = fy - b / 200
  func inv(_ t: Double) -> Double { let t3 = t * t * t; return t3 > 0.008856 ? t3 : (t - 16.0 / 116) / 7.787 }
  let X = inv(fx) * 0.95047, Y = inv(fy), Z = inv(fz) * 1.08883
  let R = 3.2406 * X - 1.5372 * Y - 0.4986 * Z, G = -0.9689 * X + 1.8758 * Y + 0.0415 * Z, B = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
  func g(_ c: Double) -> Double { let c2 = max(0, min(1, c)); return 255 * (c2 <= 0.0031308 ? 12.92 * c2 : 1.055 * pow(c2, 1 / 2.4) - 0.055) }
  return (g(R), g(G), g(B))
}
// the skin band: inside the mask, from just under the neck to just over the hips, the middle 60 % of the shoulder span (away from the arms)
func skinStats(_ buf: [UInt8], _ p: Photo) -> ([Double], [Double]) {
  let t = torso(p), n = J(p, "neck_1_joint"), r = J(p, "root")
  let xs = [J(p, "left_shoulder_1_joint").0, J(p, "right_shoulder_1_joint").0].sorted(), span = xs[1] - xs[0]
  let y0 = max(0, Int(n.1 + 0.06 * t)), y1 = min(p.h, Int(r.1 - 0.09 * t)), x0 = max(0, Int(xs[0] + 0.2 * span)), x1 = min(p.w, Int(xs[1] - 0.2 * span))
  var s = [0.0, 0.0, 0.0], q = [0.0, 0.0, 0.0], c = 0.0
  if y1 > y0 && x1 > x0 {
    for y in y0..<y1 { for x in x0..<x1 where p.mask[y * p.w + x] > 200 {
      let i = (y * p.w + x) * 4; let L = toLab(buf[i], buf[i + 1], buf[i + 2])
      s[0] += L.0; s[1] += L.1; s[2] += L.2; q[0] += L.0 * L.0; q[1] += L.1 * L.1; q[2] += L.2 * L.2; c += 1
    } }
  }
  if c < 500 { fail("SKIN NOT FOUND: the torso isn't clear in one of the photos. Use photos where the stomach and chest show.") }
  let m = s.map { $0 / c }
  return (m, (0..<3).map { sqrt(max(1e-6, q[$0] / c - m[$0] * m[$0])) })
}

// 5a. a light denoise on the before (usually the dimmer, noisier phone photo) before anything is measured
let dn = CIFilter.noiseReduction(); dn.inputImage = before.ci; dn.noiseLevel = 0.012; dn.sharpness = 0.2
var bBuf = rgba(dn.outputImage!.cropped(to: before.ci.extent))
var aBuf = rgba(after.ci)
let (mb, sb) = skinStats(bBuf, before), (ma, sa) = skinStats(aBuf, after)
// 4. lightness: a shift only (exposure). Skin colour (a, b): the after's mean and spread.
let ratio = [1.0, sa[1] / sb[1], sa[2] / sb[2]]
let gentleS: [UInt8] = (0..<256).map { i in let x = Double(i) / 255; return UInt8(max(0, min(255, (255 * (x + 0.06 * (x - 0.5) * (1 - abs(2 * x - 1)))).rounded()))) }
func finish(_ buf: inout [UInt8]) {      // one shared finish: the gentle S curve and a touch of warmth
  for i in stride(from: 0, to: buf.count, by: 4) {
    let r = Double(gentleS[Int(buf[i])]) * 1.02, g = Double(gentleS[Int(buf[i + 1])]), b = Double(gentleS[Int(buf[i + 2])]) * 0.985
    buf[i] = UInt8(min(255, r.rounded())); buf[i + 1] = UInt8(g); buf[i + 2] = UInt8(min(255, b.rounded()))
  }
}
for i in stride(from: 0, to: bBuf.count, by: 4) {
  let L = toLab(bBuf[i], bBuf[i + 1], bBuf[i + 2])
  let o = fromLab((L.0 - mb[0]) * ratio[0] + ma[0], (L.1 - mb[1]) * ratio[1] + ma[1], (L.2 - mb[2]) * ratio[2] + ma[2])
  bBuf[i] = UInt8(o.0.rounded()); bBuf[i + 1] = UInt8(o.1.rounded()); bBuf[i + 2] = UInt8(o.2.rounded())
}
finish(&bBuf); finish(&aBuf)

func sharpen(_ buf: [UInt8], _ p: Photo, _ amount: Double) -> [UInt8] {
  let u = CIFilter.unsharpMask(); u.inputImage = image(buf, p.w, p.h).clampedToExtent(); u.radius = 2.2; u.intensity = Float(amount)
  return rgba(u.outputImage!.cropped(to: CGRect(x: 0, y: 0, width: p.w, height: p.h)))
}
bBuf = sharpen(bBuf, before, 0.45); aBuf = sharpen(aBuf, after, 0.35)
let lift = ma[0] - mb[0]
if abs(lift) > 8 {   // a big exposure move stretches the photo's 8-bit steps into bands: a fine fixed grain breaks them
  var seed: UInt64 = 7
  func rnd() -> Double { seed = seed &* 6364136223846793005 &+ 1442695040888963407; return Double(seed >> 11) / Double(1 << 53) }
  for i in stride(from: 0, to: bBuf.count, by: 4) {
    let n = sqrt(-2 * log(max(1e-12, rnd()))) * cos(2 * .pi * rnd()) * 2.6
    for c in 0..<3 { bBuf[i + c] = UInt8(max(0, min(255, (Double(bBuf[i + c]) + n).rounded()))) }
  }
}

// 3. the uniform scale and the placement, then the cut-out onto the canvas
let sA = TORSO_CANVAS / torso(after), sB = sA * torso(after) / torso(before)
func centre(_ p: Photo) -> (Double, Double) { let w = waist(p); return ((w.l + w.r) / 2, (J(p, "neck_1_joint").1 + J(p, "root").1) / 2) }
func place(_ buf: [UInt8], _ p: Photo, _ s: Double, erode: Float, name: String) -> (Double, Double) {
  let c = centre(p), tx = TARGET.x - s * c.0, ty = TARGET.y - s * c.1
  var m = grayImage(p.mask, p.w, p.h).clampedToExtent()
  let er = CIFilter.morphologyMinimum(); er.inputImage = m; er.radius = erode; m = er.outputImage!
  let bl = CIFilter.gaussianBlur(); bl.inputImage = m; bl.radius = 1.4; m = bl.outputImage!.cropped(to: CGRect(x: 0, y: 0, width: p.w, height: p.h))
  let bw = CIFilter.blendWithMask(); bw.inputImage = image(buf, p.w, p.h); bw.backgroundImage = CIImage.clear; bw.maskImage = m
  var cut = bw.outputImage!.cropped(to: CGRect(x: 0, y: 0, width: p.w, height: p.h))
  let ls = CIFilter.lanczosScaleTransform(); ls.inputImage = cut; ls.scale = Float(s); ls.aspectRatio = 1; cut = ls.outputImage!
  // top-left (x, y) lands at (s x + tx, s y + ty); Core Image counts y from the bottom
  cut = cut.transformed(by: CGAffineTransform(translationX: tx, y: Double(CH) - ty - s * Double(p.h)))
  let canvas = CGRect(x: 0, y: 0, width: CW, height: CH)
  let out = cut.composited(over: CIImage.clear.cropped(to: canvas)).cropped(to: canvas)
  do { try ctx.writePNGRepresentation(of: out, to: outDir.appendingPathComponent("\(name).png"), format: .RGBA8, colorSpace: sRGB) }
  catch { fail("CAN'T WRITE the \(name) cut-out: \(error.localizedDescription)") }
  return (tx, ty)
}
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
// the before stood in a paler room in the reference pair: its fringe gets a deeper erode
_ = place(bBuf, before, sB, erode: 3, name: "before")
let (tx, ty) = place(aBuf, after, sA, erode: 2, name: "after")

// the callout points on the after's body, in 1080 x 1920 reel pixels (the canvas at 0.75)
func reel(_ q: (Double, Double)) -> [Double] { [((sA * q.0 + tx) * 0.75 * 10).rounded() / 10, ((sA * q.1 + ty) * 0.75 * 10).rounded() / 10] }
let shs = [J(after, "left_shoulder_1_joint"), J(after, "right_shoulder_1_joint")].sorted { $0.0 < $1.0 }   // image left, image right
let neck = J(after, "neck_1_joint"), root = J(after, "root"), w = waist(after)
var pts: [String: [Double]] = [:]
for (k, v) in after.joints { pts[k] = reel(v) }
pts["shoulder"] = reel((shs[0].0 + 0.03 * torso(after), shs[0].1 + 0.015 * torso(after)))   // just inside the image-left shoulder
pts["chest"] = reel((shs[1].0 + (neck.0 - shs[1].0) * 0.45 + (root.0 - neck.0) * 0.22, shs[1].1 + (neck.1 - shs[1].1) * 0.45 + (root.1 - neck.1) * 0.22))
pts["abs"] = reel((neck.0 + (root.0 - neck.0) * 0.62, neck.1 + (root.1 - neck.1) * 0.62))
pts["waist"] = reel((w.r - 0.035 * torso(after), w.y))   // just inside the waist's edge
pts["head_top"] = reel((J(after, "neck_1_joint").0, J(after, "head_joint", default: neck).1 - 0.25 * torso(after)))

let info: [String: Any] = [
  "canvas": [CW, CH], "reel": [1080, 1920],
  "before": ["crop": before.crop, "torso_px": torso(before), "scale": sB], "after": ["crop": after.crop, "torso_px": torso(after), "scale": sA],
  "skin_lab": ["before_mean": mb, "before_spread": sb, "after_mean": ma, "after_spread": sa, "exposure_shift_L": lift],
  "anchors": pts,
]
let data = try! JSONSerialization.data(withJSONObject: info, options: [.prettyPrinted, .sortedKeys])
try! data.write(to: outDir.appendingPathComponent("match.json"))
print("ok before scale \(String(format: "%.3f", sB)) after scale \(String(format: "%.3f", sA)) exposure shift L \(String(format: "%.1f", lift))")
