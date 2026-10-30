package ch.chesstour.app

import android.app.Activity
import android.os.Bundle
import android.os.Build
import android.view.WindowInsets
import android.view.View
import android.widget.FrameLayout
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
        // The WebView must occupy only the safe area, not the status/navigation bars.
        // Padding the WebView itself does not reliably move HTML on Samsung devices.
        val root = FrameLayout(this)
        root.setBackgroundColor(android.graphics.Color.rgb(245, 247, 250))
        root.addView(web, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ))
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.setDecorFitsSystemWindows(false)
            root.setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                view.setPadding(0, bars.top, 0, bars.bottom)
                insets
            }
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = 0
        }
        window.statusBarColor = android.graphics.Color.rgb(36, 59, 83)
        setContentView(root)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) root.requestApplyInsets()
        web.loadUrl("https://trdfamily.github.io/ChessTourCH/?app=0.9")
    }
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }
    override fun onDestroy() {
        web.destroy()
        super.onDestroy()
    }
}
