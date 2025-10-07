import SwiftUI
import WebKit

struct MathView: UIViewRepresentable {
    // The LaTeX equation string to be rendered
    let equation: String

    func makeUIView(context: Context) -> WKWebView {
        // Create and return a new WKWebView
        return WKWebView()
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {
        // This function is called whenever the view updates
        uiView.loadHTMLString(html(for: equation), baseURL: nil)
    }
    
    /// Generates an HTML string to render the KaTeX equation.
    private func html(for equation: String) -> String {
        // The core HTML structure
        // inside html(for:)
        let html = """
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">

          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" integrity="sha384-n8MVd4RsNIU0KOVEMeaPoSNefnRjXqbA6gP0N6UFvEouGPNiRvl/sGbGHyHNouFw" crossorigin="anonymous">
          <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8" crossorigin="anonymous"></script>

          <style>
            body {
              display: flex;
              align-items: center;
              margin: 0;
              font-size: 1.5em;
              min-height: 1px;
            }
          </style>
        </head>
        <body>
          <div id="equation"></div>
          <script>
            window.addEventListener('DOMContentLoaded', function () {
              var el = document.getElementById('equation');
              if (window.katex && el) {
                try {
                  katex.render("\(equation.escapedJavaScript)", el, { throwOnError: false });
                } catch (e) {
                  el.textContent = "\(equation.escapedJavaScript)";
                }
              } else if (el) {
                // Graceful fallback if KaTeX failed to load (e.g., no network)
                el.textContent = "\(equation.escapedJavaScript)";
              }
            });
          </script>
        </body>
        </html>
        """
        return html
    }
}

// Helper extension to properly escape strings for JavaScript
extension String {
    var escapedJavaScript: String {
        return self.replacingOccurrences(of: "\\", with: "\\\\")
                   .replacingOccurrences(of: "\"", with: "\\\"")
                   .replacingOccurrences(of: "\'", with: "\\\'")
                   .replacingOccurrences(of: "\n", with: "\\n")
                   .replacingOccurrences(of: "\r", with: "\\r")
    }
}
