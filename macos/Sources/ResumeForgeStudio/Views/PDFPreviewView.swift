import SwiftUI
import PDFKit

public struct PDFPreviewView: NSViewRepresentable {
    public let pdfPath: String?

    public init(pdfPath: String?) {
        self.pdfPath = pdfPath
    }

    public func makeNSView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.autoScales = true
        pdfView.displayMode = .singlePage
        pdfView.displaysPageBreaks = true
        pdfView.backgroundColor = NSColor(calibratedWhite: 0.12, alpha: 1.0)
        loadDocument(into: pdfView)
        return pdfView
    }

    public func updateNSView(_ nsView: PDFView, context: Context) {
        loadDocument(into: nsView)
    }

    private func loadDocument(into pdfView: PDFView) {
        guard let path = pdfPath, !path.isEmpty, FileManager.default.fileExists(atPath: path) else {
            pdfView.document = nil
            return
        }
        if pdfView.document?.documentURL?.path != path {
            pdfView.document = PDFDocument(url: URL(fileURLWithPath: path))
        }
    }
}
