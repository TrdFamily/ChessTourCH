package ch.chesstour.app

import android.app.Activity
import android.os.Bundle
import android.os.Build
import android.view.WindowInsets
import android.content.Intent
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebSettings
import android.webkit.WebResourceRequest

class MainActivity : Activity() {
    private lateinit var web: WebView
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.cacheMode = WebSettings.LOAD_NO_CACHE
        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url ?: return false
                val internal = url.scheme == "https" && url.host == "trdfamily.github.io" &&
                    (url.path ?: "").startsWith("/ChessTourCH/")
                if (internal) return false
                if (url.scheme == "https" || url.scheme == "geo") {
                    try { startActivity(Intent(Intent.ACTION_VIEW, url)) } catch (_: Exception) {}
                }
                return true
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            web.setOnApplyWindowInsetsListener { view, insets ->
                val top = insets.getInsets(WindowInsets.Type.statusBars()).top
                view.setPadding(0, top, 0, 0)
                insets
            }
        }
        window.statusBarColor = android.graphics.Color.rgb(36, 59, 83)
        setContentView(web)
        web.loadUrl("https://trdfamily.github.io/ChessTourCH/?app=0.7")
    }
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
    override fun onDestroy() {
        web.destroy()
        super.onDestroy()
    }
}
