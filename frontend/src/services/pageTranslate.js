// Whole-website translation.
//
// i18next (src/i18n.js) only translates strings that use t(...), which is why
// only the sidebar/panel changed language. This service translates the ENTIRE
// rendered page (every page, buttons, toasts, API data) using Google's website
// translation engine, driven by the language the user picks in the app.
//
// "hi-latn" (Hinglish) is not a real Google language, so it keeps the page in
// English (the AI chat still answers in Hinglish through the backend).

const SOURCE_LANG = 'en'
export const TRANSLATABLE = ['hi', 'mr', 'ta', 'te', 'kn', 'ml', 'gu', 'bn', 'pa', 'ur']
const RTL = ['ur']

let loadPromise = null
let patched = false

// Google Translate rewrites text nodes, which makes React throw
// "Failed to execute 'removeChild' on 'Node'" on the next re-render.
// These two guards are the standard fix.
function patchDomForReact() {
  if (patched || typeof Node === 'undefined') return
  patched = true

  const originalRemoveChild = Node.prototype.removeChild
  Node.prototype.removeChild = function (child) {
    if (child && child.parentNode !== this) {
      // Google moved this text node inside a <font> wrapper. Remove it from
      // where it really lives (instead of silently skipping, which left stale
      // copies behind and showed the same label 2-3 times).
      if (child.parentNode) return originalRemoveChild.call(child.parentNode, child)
      return child
    }
    return originalRemoveChild.apply(this, arguments)
  }

  const originalInsertBefore = Node.prototype.insertBefore
  Node.prototype.insertBefore = function (newNode, referenceNode) {
    if (referenceNode && referenceNode.parentNode !== this) {
      if (referenceNode.parentNode) {
        return originalInsertBefore.call(referenceNode.parentNode, newNode, referenceNode)
      }
      return originalInsertBefore.call(this, newNode, null)
    }
    return originalInsertBefore.apply(this, arguments)
  }
}

function ensureHost() {
  if (document.getElementById('google_translate_element')) return
  const host = document.createElement('div')
  host.id = 'google_translate_element'
  host.style.display = 'none'
  host.setAttribute('translate', 'no')
  document.body.appendChild(host)
}

function loadEngine() {
  if (loadPromise) return loadPromise
  loadPromise = new Promise((resolve, reject) => {
    ensureHost()
    window.googleTranslateElementInit = () => {
      try {
        // eslint-disable-next-line no-new
        new window.google.translate.TranslateElement(
          {
            pageLanguage: SOURCE_LANG,
            includedLanguages: TRANSLATABLE.join(','),
            autoDisplay: false,
          },
          'google_translate_element'
        )
        resolve()
      } catch (err) {
        reject(err)
      }
    }
    const script = document.createElement('script')
    script.src =
      'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit'
    script.async = true
    script.onerror = () => {
      loadPromise = null // allow retry later
      reject(new Error('Translation engine failed to load'))
    }
    document.head.appendChild(script)
  })
  return loadPromise
}

function setCookie(value) {
  const host = window.location.hostname
  const base = `googtrans=${value}; path=/`
  document.cookie = base
  // some browsers need the domain-scoped copy too
  if (host && host !== 'localhost') document.cookie = `${base}; domain=${host}`
}

function clearCookie() {
  const expired = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/'
  document.cookie = expired
  const host = window.location.hostname
  if (host && host !== 'localhost') document.cookie = `${expired}; domain=${host}`
}

function waitForCombo(timeoutMs = 6000) {
  return new Promise((resolve) => {
    const started = Date.now()
    const tick = () => {
      const combo = document.querySelector('select.goog-te-combo')
      if (combo) return resolve(combo)
      if (Date.now() - started > timeoutMs) return resolve(null)
      setTimeout(tick, 100)
    }
    tick()
  })
}

function currentCookieLang() {
  const match = document.cookie.match(/(?:^|;\s*)googtrans=\/[^/]+\/([^;]+)/)
  return match ? match[1] : SOURCE_LANG
}

function setDocumentLang(code) {
  document.documentElement.lang = code
  document.documentElement.dir = RTL.includes(code) ? 'rtl' : 'ltr'
}

/**
 * Translate the whole site into `code` (any key of the app's LANGUAGES list).
 * Safe to call repeatedly; no-ops when the page is already in that language.
 */
export async function applyPageLanguage(code) {
  if (typeof window === 'undefined') return

  const target = TRANSLATABLE.includes(code) ? code : SOURCE_LANG
  const active = currentCookieLang()

  // Back to English: Google's own restore needs a reload to be reliable.
  if (target === SOURCE_LANG) {
    if (active !== SOURCE_LANG) {
      clearCookie()
      setDocumentLang(SOURCE_LANG)
      window.location.reload()
    } else {
      setDocumentLang(SOURCE_LANG)
    }
    return
  }

  if (active === target && document.querySelector('html.translated-ltr, html.translated-rtl')) {
    setDocumentLang(target)
    return
  }

  patchDomForReact()
  setCookie(`/${SOURCE_LANG}/${target}`)

  try {
    await loadEngine()
    const combo = await waitForCombo()
    if (!combo) throw new Error('Language selector not ready')
    combo.value = target
    combo.dispatchEvent(new Event('change'))
    setDocumentLang(target)
  } catch (err) {
    // Last resort: a reload lets the cookie drive the translation on startup.
    console.warn('[pageTranslate]', err)
  }
}

/** Call once at app start so a saved language is applied to the whole site. */
export function initPageTranslation(savedLang) {
  patchDomForReact()
  if (TRANSLATABLE.includes(savedLang)) {
    applyPageLanguage(savedLang)
  } else {
    clearCookie()
    setDocumentLang(SOURCE_LANG)
  }
}
