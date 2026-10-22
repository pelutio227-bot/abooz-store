import UIKit
import Capacitor
import VisionKit
import AuthenticationServices
import CryptoKit

/// Bridge-ViewController: registriert das lokale Plugin «AboozNative».
class AboozBridgeViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        bridge?.registerPluginInstance(AboozNativePlugin())
        // iOS-typisch: Seite federt immer nach (auch wenn der Inhalt kürzer als der Bildschirm ist)
        webView?.scrollView.bounces = true
        webView?.scrollView.alwaysBounceVertical = true
        webView?.scrollView.contentInsetAdjustmentBehavior = .never
    }
}

/// Native Zusatzfunktionen für abooz.ch (vom Web via window.Capacitor.Plugins.AboozNative):
/// - scanDocument(): Dokumenten-Scanner (VisionKit) → { images: [base64-JPEG] }
/// - signInWithApple({ nonce? }): Sign in with Apple → { identityToken, authorizationCode, email, givenName, familyName }
@objc(AboozNativePlugin)
public class AboozNativePlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "AboozNativePlugin"
    public let jsName = "AboozNative"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "scanDocument", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "signInWithApple", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "isAvailable", returnType: CAPPluginReturnPromise),
    ]

    private var scanCall: CAPPluginCall?
    private var appleCall: CAPPluginCall?

    @objc func isAvailable(_ call: CAPPluginCall) {
        call.resolve([
            "scanner": VNDocumentCameraViewController.isSupported,
            "appleSignIn": true,
        ])
    }

    // MARK: Dokumenten-Scanner

    @objc func scanDocument(_ call: CAPPluginCall) {
        guard VNDocumentCameraViewController.isSupported else {
            call.reject("Der Dokumenten-Scanner ist auf diesem Gerät nicht verfügbar.", "unsupported")
            return
        }
        DispatchQueue.main.async {
            self.scanCall = call
            let scanner = VNDocumentCameraViewController()
            scanner.delegate = self
            scanner.modalPresentationStyle = .fullScreen
            self.bridge?.viewController?.present(scanner, animated: true)
        }
    }

    fileprivate static func encode(_ image: UIImage, maxEdge: CGFloat = 2000, quality: CGFloat = 0.7) -> String? {
        let size = image.size
        let longest = max(size.width, size.height)
        var target = image
        if longest > maxEdge {
            let scale = maxEdge / longest
            let newSize = CGSize(width: floor(size.width * scale), height: floor(size.height * scale))
            let format = UIGraphicsImageRendererFormat()
            format.scale = 1
            target = UIGraphicsImageRenderer(size: newSize, format: format).image { _ in
                image.draw(in: CGRect(origin: .zero, size: newSize))
            }
        }
        return target.jpegData(compressionQuality: quality)?.base64EncodedString()
    }

    // MARK: Sign in with Apple

    @objc func signInWithApple(_ call: CAPPluginCall) {
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.fullName, .email]
        if let nonce = call.getString("nonce"), !nonce.isEmpty {
            let digest = SHA256.hash(data: Data(nonce.utf8))
            request.nonce = digest.map { String(format: "%02x", $0) }.joined()
        }
        DispatchQueue.main.async {
            self.appleCall = call
            let controller = ASAuthorizationController(authorizationRequests: [request])
            controller.delegate = self
            controller.presentationContextProvider = self
            controller.performRequests()
        }
    }
}

extension AboozNativePlugin: VNDocumentCameraViewControllerDelegate {
    public func documentCameraViewController(_ controller: VNDocumentCameraViewController, didFinishWith scan: VNDocumentCameraScan) {
        let pages = scan.pageCount
        controller.dismiss(animated: true)
        guard let call = scanCall else { return }
        scanCall = nil
        DispatchQueue.global(qos: .userInitiated).async {
            var images: [String] = []
            for i in 0..<pages {
                if let b64 = AboozNativePlugin.encode(scan.imageOfPage(at: i)) { images.append(b64) }
            }
            call.resolve(["images": images])
        }
    }

    public func documentCameraViewControllerDidCancel(_ controller: VNDocumentCameraViewController) {
        controller.dismiss(animated: true)
        scanCall?.reject("cancelled", "cancelled")
        scanCall = nil
    }

    public func documentCameraViewController(_ controller: VNDocumentCameraViewController, didFailWithError error: Error) {
        controller.dismiss(animated: true)
        scanCall?.reject(error.localizedDescription, "failed", error)
        scanCall = nil
    }
}

extension AboozNativePlugin: ASAuthorizationControllerDelegate, ASAuthorizationControllerPresentationContextProviding {
    public func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        return bridge?.viewController?.view.window ?? ASPresentationAnchor()
    }

    public func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        guard let call = appleCall else { return }
        appleCall = nil
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
              let tokenData = credential.identityToken,
              let token = String(data: tokenData, encoding: .utf8) else {
            call.reject("Kein Apple-Token erhalten.", "failed")
            return
        }
        var result: [String: Any] = ["identityToken": token, "user": credential.user]
        if let code = credential.authorizationCode, let s = String(data: code, encoding: .utf8) { result["authorizationCode"] = s }
        if let email = credential.email { result["email"] = email }
        if let given = credential.fullName?.givenName { result["givenName"] = given }
        if let family = credential.fullName?.familyName { result["familyName"] = family }
        call.resolve(result)
    }

    public func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        guard let call = appleCall else { return }
        appleCall = nil
        if let e = error as? ASAuthorizationError, e.code == .canceled {
            call.reject("cancelled", "cancelled")
        } else {
            call.reject(error.localizedDescription, "failed", error)
        }
    }
}
