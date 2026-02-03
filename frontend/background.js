// API configuration
const API_URL = "http://localhost:8010";
const FACTCHECK_API_URL = "http://localhost:8016";

// Open the side panel
chrome.sidePanel.setOptions({
    path: "index.html",
});

// Initialize extension on install
chrome.runtime.onInstalled.addListener(() => {
    // Don't auto-open side panel on click (we use popup now)
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });

    // Create context menu for fact-checking (initially hidden, shown only on news sites)
    chrome.contextMenus.create({
        id: "factcheck-selection",
        title: "Fact-check this claim",
        contexts: ["selection"],
        visible: false
    });

    // Initialize default settings
    chrome.storage.sync.get(['pageOverlayEnabled', 'contextMenuEnabled'], (result) => {
        if (result.pageOverlayEnabled === undefined) {
            chrome.storage.sync.set({ pageOverlayEnabled: false });
        }
        if (result.contextMenuEnabled === undefined) {
            chrome.storage.sync.set({ contextMenuEnabled: true });
        }
    });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    console.log("[Checkmate] Context menu clicked:", info.menuItemId);

    if (info.menuItemId === "factcheck-selection") {
        // Check if context menu is enabled
        const { contextMenuEnabled } = await chrome.storage.sync.get('contextMenuEnabled');
        console.log("[Checkmate] Context menu enabled:", contextMenuEnabled);

        if (contextMenuEnabled === false) {
            console.log("[Checkmate] Context menu is disabled, ignoring");
            return;
        }

        const selectedText = info.selectionText;
        console.log("[Checkmate] Selected text:", selectedText?.substring(0, 50) + "...");

        if (selectedText && selectedText.trim().length > 0) {
            console.log("[Checkmate] Starting fact-check for tab:", tab.id);
            await performFactCheck(tab, selectedText.trim(), info.pageUrl);
        }
    }
});

/**
 * Inject the fact-check content script into the tab
 * @param {number} tabId - The tab ID to inject into
 */
async function injectFactCheckScript(tabId) {
    try {
        console.log("[Checkmate] Attempting to inject content script into tab:", tabId);

        // Check if script is already injected
        const results = await chrome.scripting.executeScript({
            target: { tabId },
            func: () => window.__factcheckContentScriptLoaded
        });

        if (results && results[0] && results[0].result) {
            console.log("[Checkmate] Content script already injected");
            return true;
        }

        // Inject the content script inline
        console.log("[Checkmate] Injecting content script...");
        await chrome.scripting.executeScript({
            target: { tabId },
            func: injectFactCheckTooltipScript
        });

        console.log("[Checkmate] Content script injected successfully");
        return true;
    } catch (error) {
        console.error("[Checkmate] Error injecting fact-check script:", error);
        console.error("[Checkmate] Error details:", error.message);
        return false;
    }
}

/**
 * Inline content script function for fact-check tooltip
 * This gets serialized and injected into the page
 */
function injectFactCheckTooltipScript() {
    // Prevent multiple injections
    if (window.__factcheckContentScriptLoaded) return;
    window.__factcheckContentScriptLoaded = true;

    const TOOLTIP_ID = 'checkmate-factcheck-tooltip';
    let lastSelectionRect = null;

    // Capture selection position
    document.addEventListener('mouseup', () => {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length > 0) {
            const range = selection.getRangeAt(0);
            lastSelectionRect = range.getBoundingClientRect();
        }
    });

    document.addEventListener('contextmenu', () => {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length > 0) {
            const range = selection.getRangeAt(0);
            lastSelectionRect = range.getBoundingClientRect();
        }
    });

    // Inject styles
    function injectStyles() {
        if (document.getElementById('checkmate-factcheck-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'checkmate-factcheck-styles';
        styles.textContent = `
            #${TOOLTIP_ID} {
                position: fixed;
                z-index: 2147483647;
                max-width: 380px;
                min-width: 300px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(0, 0, 0, 0.05);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.5;
                color: #1f2937;
                animation: checkmate-fadein 0.2s ease-out;
            }
            @keyframes checkmate-fadein {
                from { opacity: 0; transform: translateY(-8px); }
                to { opacity: 1; transform: translateY(0); }
            }
            #${TOOLTIP_ID} * { box-sizing: border-box; }
            .checkmate-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                border-bottom: 1px solid #e5e7eb;
                background: #f9fafb;
                border-radius: 12px 12px 0 0;
            }
            .checkmate-header-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                font-size: 13px;
                color: #374151;
            }
            .checkmate-close-btn {
                background: none;
                border: none;
                cursor: pointer;
                padding: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                color: #6b7280;
                transition: all 0.15s;
            }
            .checkmate-close-btn:hover {
                background: #e5e7eb;
                color: #1f2937;
            }
            .checkmate-content { padding: 16px; }
            .checkmate-loading {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 24px 16px;
                gap: 12px;
            }
            .checkmate-spinner {
                width: 32px;
                height: 32px;
                border: 3px solid #e5e7eb;
                border-top-color: #3b82f6;
                border-radius: 50%;
                animation: checkmate-spin 0.8s linear infinite;
            }
            @keyframes checkmate-spin { to { transform: rotate(360deg); } }
            .checkmate-loading-text { color: #6b7280; font-size: 13px; }
            .checkmate-claim {
                background: #f3f4f6;
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 12px;
                font-size: 13px;
                color: #4b5563;
                border-left: 3px solid #9ca3af;
            }
            .checkmate-claim-label {
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #6b7280;
                margin-bottom: 4px;
            }
            .checkmate-verdict {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 12px;
            }
            .checkmate-verdict-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 13px;
            }
            .checkmate-verdict-factual { background: #dcfce7; color: #166534; }
            .checkmate-verdict-unfactual { background: #fee2e2; color: #991b1b; }
            .checkmate-verdict-undetermined { background: #fef3c7; color: #92400e; }
            .checkmate-explanation { font-size: 13px; color: #4b5563; margin-bottom: 12px; }
            .checkmate-citations { border-top: 1px solid #e5e7eb; padding-top: 12px; }
            .checkmate-citations-title {
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #6b7280;
                margin-bottom: 8px;
            }
            .checkmate-citation-link {
                display: block;
                padding: 6px 0;
                color: #2563eb;
                text-decoration: none;
                font-size: 12px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .checkmate-citation-link:hover { text-decoration: underline; }
            .checkmate-error { color: #dc2626; text-align: center; padding: 16px; }
            .checkmate-error-icon { font-size: 24px; margin-bottom: 8px; }
        `;
        document.head.appendChild(styles);
    }

    function getVerdictInfo(correctness) {
        const normalized = (correctness || '').toLowerCase().trim();
        if (normalized === 'factual' || (normalized.includes('factual') && !normalized.includes('unfactual'))) {
            return { class: 'checkmate-verdict-factual', icon: '\u2705', label: 'Factual' };
        } else if (normalized === 'unfactual' || normalized.includes('unfactual') || normalized.includes('false')) {
            return { class: 'checkmate-verdict-unfactual', icon: '\u274C', label: 'Unfactual' };
        }
        return { class: 'checkmate-verdict-undetermined', icon: '\u2753', label: 'Cannot Be Determined' };
    }

    function removeTooltip() {
        const existing = document.getElementById(TOOLTIP_ID);
        if (existing) existing.remove();
    }

    function createTooltip() {
        removeTooltip();
        injectStyles();
        const tooltip = document.createElement('div');
        tooltip.id = TOOLTIP_ID;
        document.body.appendChild(tooltip);
        return tooltip;
    }

    function positionTooltip(tooltip) {
        if (!lastSelectionRect) {
            tooltip.style.left = '50%';
            tooltip.style.top = '20%';
            tooltip.style.transform = 'translateX(-50%)';
            return;
        }
        const rect = lastSelectionRect;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const tooltipRect = tooltip.getBoundingClientRect();
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        let top = rect.bottom + 10;
        if (left < 10) left = 10;
        if (left + tooltipRect.width > viewportWidth - 10) left = viewportWidth - tooltipRect.width - 10;
        if (top + tooltipRect.height > viewportHeight - 10) top = rect.top - tooltipRect.height - 10;
        if (top < 10) top = 10;
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showLoading() {
        const tooltip = createTooltip();
        tooltip.innerHTML = `
            <div class="checkmate-header">
                <div class="checkmate-header-title">
                    <span>\u265F</span>
                    <span>Checkmate Fact-Check</span>
                </div>
                <button class="checkmate-close-btn" aria-label="Close">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="checkmate-loading">
                <div class="checkmate-spinner"></div>
                <div class="checkmate-loading-text">Verifying claim...</div>
            </div>
        `;
        tooltip.querySelector('.checkmate-close-btn').addEventListener('click', removeTooltip);
        requestAnimationFrame(() => positionTooltip(tooltip));
    }

    function showResults(data) {
        const tooltip = document.getElementById(TOOLTIP_ID) || createTooltip();
        const verdictInfo = getVerdictInfo(data.correctness);
        let citationsHtml = '';
        if (data.citations && data.citations.length > 0) {
            const citationLinks = data.citations.map((citation, index) => {
                const url = typeof citation === 'string' ? citation : citation.url || citation.source || '';
                if (!url) return '';
                let displayText = url;
                try {
                    const urlObj = new URL(url);
                    displayText = urlObj.hostname.replace('www.', '');
                } catch { displayText = url.slice(0, 50) + (url.length > 50 ? '...' : ''); }
                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="checkmate-citation-link">[${index + 1}] ${displayText}</a>`;
            }).filter(Boolean).join('');
            if (citationLinks) {
                citationsHtml = `<div class="checkmate-citations"><div class="checkmate-citations-title">Sources</div>${citationLinks}</div>`;
            }
        }
        tooltip.innerHTML = `
            <div class="checkmate-header">
                <div class="checkmate-header-title">
                    <span>\u265F</span>
                    <span>Checkmate Fact-Check</span>
                </div>
                <button class="checkmate-close-btn" aria-label="Close">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="checkmate-content">
                <div class="checkmate-claim">
                    <div class="checkmate-claim-label">Claim</div>
                    ${escapeHtml(data.claim || '')}
                </div>
                <div class="checkmate-verdict">
                    <span class="checkmate-verdict-badge ${verdictInfo.class}">
                        ${verdictInfo.icon} ${verdictInfo.label}
                    </span>
                </div>
                <div class="checkmate-explanation">${escapeHtml(data.explanation || 'No explanation available.')}</div>
                ${citationsHtml}
            </div>
        `;
        tooltip.querySelector('.checkmate-close-btn').addEventListener('click', removeTooltip);
        requestAnimationFrame(() => positionTooltip(tooltip));
    }

    function showError(message) {
        const tooltip = document.getElementById(TOOLTIP_ID) || createTooltip();
        tooltip.innerHTML = `
            <div class="checkmate-header">
                <div class="checkmate-header-title">
                    <span>\u265F</span>
                    <span>Checkmate Fact-Check</span>
                </div>
                <button class="checkmate-close-btn" aria-label="Close">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="checkmate-error">
                <div class="checkmate-error-icon">\u26A0\uFE0F</div>
                <div>${escapeHtml(message)}</div>
            </div>
        `;
        tooltip.querySelector('.checkmate-close-btn').addEventListener('click', removeTooltip);
        requestAnimationFrame(() => positionTooltip(tooltip));
    }

    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        console.log('[Checkmate Content] Received message:', message.action);
        if (message.action === 'factcheckLoading') {
            showLoading();
            sendResponse({ success: true });
        } else if (message.action === 'factcheckResult') {
            showResults(message.data);
            sendResponse({ success: true });
        } else if (message.action === 'factcheckError') {
            showError(message.error);
            sendResponse({ success: true });
        } else if (message.action === 'closeFactcheckTooltip') {
            removeTooltip();
            sendResponse({ success: true });
        }
        return true;
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        const tooltip = document.getElementById(TOOLTIP_ID);
        if (tooltip && !tooltip.contains(e.target)) removeTooltip();
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') removeTooltip();
    });

    console.log('[Checkmate] Fact-check content script loaded');
}

/**
 * Perform fact-check on selected text
 * @param {Object} tab - The tab object
 * @param {string} claim - The selected text/claim to fact-check
 * @param {string} pageUrl - The URL of the page
 */
async function performFactCheck(tab, claim, pageUrl) {
    try {
        // Inject the content script
        const injected = await injectFactCheckScript(tab.id);
        if (!injected) {
            console.error("Could not inject fact-check script");
            return;
        }

        // Small delay to ensure script is ready
        await new Promise(resolve => setTimeout(resolve, 100));

        // Show loading state in content script
        await chrome.tabs.sendMessage(tab.id, {
            action: 'factcheckLoading',
            claim: claim
        });

        // Call the fact-check API
        console.log("[Checkmate] Calling fact-check API:", `${FACTCHECK_API_URL}/factcheck/claim`);
        console.log("[Checkmate] Request payload:", { claim: claim.substring(0, 50), page_title: tab.title, page_url: pageUrl });

        let response;
        try {
            response = await fetch(`${FACTCHECK_API_URL}/factcheck/claim`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    claim: claim,
                    page_title: tab.title || '',
                    page_url: pageUrl || tab.url || ''
                })
            });
        } catch (fetchError) {
            console.error("[Checkmate] Fetch failed:", fetchError);
            throw new Error(`Network error: ${fetchError.message}. Is the fact-check service running on port 8005?`);
        }

        console.log("[Checkmate] API response status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("[Checkmate] API error response:", errorText);
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log("[Checkmate] API response data:", data);

        if (data && data.response) {
            // Send results to content script
            await chrome.tabs.sendMessage(tab.id, {
                action: 'factcheckResult',
                data: data.response
            });
        } else {
            throw new Error('Invalid response from fact-check service');
        }

    } catch (error) {
        console.error("Fact-check error:", error);

        // Send error to content script
        try {
            await chrome.tabs.sendMessage(tab.id, {
                action: 'factcheckError',
                error: error.message || 'Failed to verify claim. Please try again.'
            });
        } catch (sendError) {
            console.error("Could not send error to content script:", sendError);
        }
    }
}

console.log("Background script loaded");

let tabUrl = null;

// =============================================================================
// Badge Helper Functions
// =============================================================================

/**
 * Get propaganda level label based on percentage
 * @param {number} percentage - Propaganda percentage (0-100)
 * @returns {string} Level label (Low, Moderate, High)
 */
function getPropagandaLevel(percentage) {
    if (percentage <= 30) return "Low";
    if (percentage <= 60) return "Moderate";
    return "High";
}

/**
 * Get badge background color based on propaganda percentage
 * @param {number} percentage - Propaganda percentage (0-100)
 * @returns {string} Hex color code
 */
function getBadgeColor(percentage) {
    if (percentage <= 30) return "#22C55E"; // Green
    if (percentage <= 60) return "#EAB308"; // Yellow
    return "#EF4444"; // Red
}

/**
 * Set badge to show propaganda level with color coding
 * @param {number} propagandaProbability - Propaganda probability (0-1)
 * @param {number} tabId - Optional specific tab ID
 */
async function setBadgeForPropaganda(propagandaProbability, tabId = null) {
    const percentage = Math.round(propagandaProbability * 100);
    const level = getPropagandaLevel(percentage);
    const color = getBadgeColor(percentage);

    const badgeText = `${percentage}%`;
    const tooltipText = `Propaganda: ${level} (${percentage}%) - Click for details`;

    try {
        if (tabId) {
            await chrome.action.setBadgeText({ text: badgeText, tabId });
            await chrome.action.setBadgeBackgroundColor({ color, tabId });
            await chrome.action.setTitle({ title: tooltipText, tabId });
        } else {
            await chrome.action.setBadgeText({ text: badgeText });
            await chrome.action.setBadgeBackgroundColor({ color });
            await chrome.action.setTitle({ title: tooltipText });
        }
    } catch (error) {
        console.error("Error setting badge:", error);
    }
}

/**
 * Set badge to loading state (...)
 * @param {number} tabId - Optional specific tab ID
 */
async function setLoadingBadge(tabId = null) {
    try {
        if (tabId) {
            await chrome.action.setBadgeText({ text: "...", tabId });
            await chrome.action.setBadgeBackgroundColor({ color: "#6B7280", tabId }); // Gray
            await chrome.action.setTitle({ title: "Analyzing article...", tabId });
        } else {
            await chrome.action.setBadgeText({ text: "..." });
            await chrome.action.setBadgeBackgroundColor({ color: "#6B7280" }); // Gray
            await chrome.action.setTitle({ title: "Analyzing article..." });
        }
    } catch (error) {
        console.error("Error setting loading badge:", error);
    }
}

/**
 * Clear the badge (reset to default)
 * @param {number} tabId - Optional specific tab ID
 */
async function clearBadge(tabId = null) {
    try {
        if (tabId) {
            await chrome.action.setBadgeText({ text: "", tabId });
            await chrome.action.setTitle({ title: "FrontEnd", tabId });
        } else {
            await chrome.action.setBadgeText({ text: "" });
            await chrome.action.setTitle({ title: "FrontEnd" });
        }
    } catch (error) {
        console.error("Error clearing badge:", error);
    }
}

// =============================================================================
// URL Detection & Caching
// =============================================================================

/**
 * Check if a URL is likely a news article
 * Comprehensive detection matching PopupPage.jsx
 * @param {string} url - The URL to check
 * @returns {boolean} True if likely a news article
 */
function isLikelyNewsUrl(url) {
    if (!url) return false;

    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname.toLowerCase();
        const pathname = urlObj.pathname.toLowerCase();
        const fullUrl = url.toLowerCase();

        // Skip browser-specific URLs
        const skipPatterns = [
            /^chrome:\/\//,
            /^chrome-extension:\/\//,
            /^about:/,
            /^file:/,
            /^edge:\/\//,
            /^moz-extension:\/\//,
        ];

        for (const pattern of skipPatterns) {
            if (pattern.test(url)) return false;
        }

        // Blocklist: domains that are definitely NOT news sites
        const nonNewsDomains = [
            // Social media
            /^(www\.)?(facebook|fb)\.com$/,
            /^(www\.)?twitter\.com$/,
            /^(www\.)?x\.com$/,
            /^(www\.)?instagram\.com$/,
            /^(www\.)?tiktok\.com$/,
            /^(www\.)?snapchat\.com$/,
            /^(www\.)?pinterest\.com$/,
            /^(www\.)?linkedin\.com$/,
            /^(www\.)?reddit\.com$/,
            /^(www\.)?discord\.(com|gg)$/,
            /^(www\.)?threads\.net$/,
            // Video/streaming platforms
            /^(www\.)?(youtube|youtu\.be)\.com$/,
            /^(www\.)?netflix\.com$/,
            /^(www\.)?hulu\.com$/,
            /^(www\.)?twitch\.tv$/,
            /^(www\.)?vimeo\.com$/,
            /^(www\.)?dailymotion\.com$/,
            /^(www\.)?disneyplus\.com$/,
            /^(www\.)?primevideo\.com$/,
            /^(www\.)?spotify\.com$/,
            // E-commerce
            /^(www\.)?amazon\.(com|co\.[a-z]+|[a-z]+)$/,
            /^(www\.)?ebay\.(com|co\.[a-z]+|[a-z]+)$/,
            /^(www\.)?aliexpress\.com$/,
            /^(www\.)?alibaba\.com$/,
            /^(www\.)?etsy\.com$/,
            /^(www\.)?shopify\.com$/,
            /^(www\.)?walmart\.com$/,
            /^(www\.)?target\.com$/,
            /^(www\.)?bestbuy\.com$/,
            /^(.*\.)?shopee\.(com|sg|my|ph|[a-z]+)$/,
            /^(www\.)?lazada\.(com|sg|my|ph|[a-z]+)$/,
            // Developer/tech platforms
            /^(www\.)?github\.com$/,
            /^(www\.)?gitlab\.com$/,
            /^(www\.)?bitbucket\.org$/,
            /^(www\.)?stackoverflow\.com$/,
            /^(www\.)?stackexchange\.com$/,
            /^(www\.)?codepen\.io$/,
            /^(www\.)?jsfiddle\.net$/,
            /^(www\.)?replit\.com$/,
            /^(www\.)?npmjs\.com$/,
            /^(www\.)?pypi\.org$/,
            /^(www\.)?vercel\.com$/,
            /^(www\.)?netlify\.com$/,
            // Backend/Database services
            /^(.*\.)?supabase\.(com|co|io)$/,
            /^(.*\.)?firebase\.google\.com$/,
            /^(.*\.)?firebaseio\.com$/,
            // Cloud platforms
            /^(.*\.)?aws\.amazon\.com$/,
            /^(.*\.)?azure\.com$/,
            /^(.*\.)?cloud\.google\.com$/,
            // Productivity/tools
            /^(www\.)?google\.(com|co\.[a-z]+|[a-z]+)$/,
            /^(mail|drive|docs|sheets|calendar)\.google\.com$/,
            /^(www\.)?notion\.so$/,
            /^(www\.)?trello\.com$/,
            /^(www\.)?slack\.com$/,
            /^(www\.)?zoom\.us$/,
            /^(www\.)?dropbox\.com$/,
            /^(www\.)?figma\.com$/,
            /^(www\.)?canva\.com$/,
            // AI platforms
            /^(www\.)?openai\.com$/,
            /^(www\.)?anthropic\.com$/,
            /^(www\.)?claude\.ai$/,
            /^(www\.)?chat\.openai\.com$/,
            // Search engines
            /^(www\.)?bing\.com$/,
            /^(www\.)?duckduckgo\.com$/,
            /^(www\.)?yahoo\.com$/,
            /^search\./,
            // Other non-news
            /^(www\.)?wikipedia\.org$/,
            /^[a-z]+\.wikipedia\.org$/,
            /^(www\.)?imdb\.com$/,
            /^(www\.)?quora\.com$/,
            /^(www\.)?medium\.com$/,
            /^localhost(:\d+)?$/,
            /^127\.0\.0\.1(:\d+)?$/,
        ];

        for (const pattern of nonNewsDomains) {
            if (pattern.test(hostname)) return false;
        }

        // Non-article URL patterns
        const nonArticlePatterns = [
            /\/(login|signin|signup|register|logout|account|profile|settings)\/?$/i,
            /\/(cart|checkout|basket|wishlist|orders?)\/?$/i,
            /\/(search|results|browse|explore)\/?$/i,
            /\/(category|categories|tag|tags|archive|archives|topics?)\/?$/i,
            /^\/?$/,
            /\/?(index|home|about|contact|privacy|terms|faq|help|support)\/?$/i,
            /\/(products?|shop|store|buy|pricing|plans?|subscribe)\/?$/i,
            /\/(download|install|apps?)\/?$/i,
            /\/(video|videos|watch|playlist|channel|live)\/?$/i,
            /\/(photos?|images?|gallery|galleries|media)\/?$/i,
            /\/(jobs?|careers?|hiring)\/?$/i,
            /\/(auth|oauth|callback|verify|confirm)\/?$/i,
            /\/(api|graphql|webhook)\/?/i,
            /\.(jpg|jpeg|png|gif|webp|svg|pdf|mp4|mp3|zip|exe)$/i,
            /^\/(news|world|politics|business|economy|sports?|entertainment|health|science|technology|tech|opinion|editorial|lifestyle|travel|food|culture|money|weather|video|live|latest|trending|popular|top-stories?)\/?$/i,
            /^\/(us|uk|asia|europe|africa|americas|middle-east|australia)\/?$/i,
            /^\/(local|national|international|global)\/?$/i,
        ];

        for (const pattern of nonArticlePatterns) {
            if (pattern.test(pathname)) return false;
        }

        // Known news domain patterns (allowlist)
        const newsDomainsPatterns = [
            /^(www\.)?(bbc\.(com|co\.uk)|cnn\.com|reuters\.com|apnews\.com)$/,
            /^(www\.)?(nytimes\.com|washingtonpost\.com|theguardian\.com)$/,
            /^(www\.)?(wsj\.com|ft\.com|economist\.com|bloomberg\.com)$/,
            /^(www\.)?(nbcnews\.com|cbsnews\.com|abcnews\.go\.com|foxnews\.com)$/,
            /^(www\.)?(npr\.org|pbs\.org|aljazeera\.com)$/,
            /^(www\.)?(usatoday\.com|latimes\.com|nypost\.com|politico\.com)$/,
            /^(www\.)?(thehill\.com|axios\.com|vox\.com|buzzfeednews\.com)$/,
            /^(www\.)?(independent\.co\.uk|telegraph\.co\.uk|dailymail\.co\.uk)$/,
            /^(www\.)?(forbes\.com|businessinsider\.com|cnbc\.com)$/,
            /^(www\.)?(huffpost\.com|huffingtonpost\.com|theatlantic\.com)$/,
            /^(www\.)?(time\.com|newsweek\.com|usnews\.com)$/,
            /^(www\.)?(straitstimes\.com|channelnewsasia\.com|todayonline\.com)$/,
            /^(www\.)?(scmp\.com|asia\.nikkei\.com|japantimes\.co\.jp)$/,
            /^(www\.)?(koreaherald\.com|koreatimes\.co\.kr)$/,
            /^(www\.)?(thehindu\.com|indianexpress\.com|hindustantimes\.com)$/,
            /^(www\.)?(abc\.net\.au|news\.com\.au|smh\.com\.au)$/,
            /^(www\.)?(techcrunch\.com|theverge\.com|wired\.com|arstechnica\.com)$/,
            /^(www\.)?(engadget\.com|gizmodo\.com|mashable\.com|cnet\.com)$/,
            /^(www\.)?(zdnet\.com|venturebeat\.com|techradar\.com)$/,
        ];

        const isKnownNewsDomain = newsDomainsPatterns.some((pattern) =>
            pattern.test(hostname)
        );

        if (isKnownNewsDomain) {
            const pathParts = pathname.split("/").filter((p) => p.length > 0);
            if (pathParts.length >= 2) return true;
            if (pathParts.length === 1) {
                const slug = pathParts[0];
                const looksLikeArticleSlug = slug.length > 25 && slug.includes("-");
                return looksLikeArticleSlug;
            }
            return false;
        }

        // News indicator patterns for unknown domains
        const newsIndicatorPatterns = [
            /\/\d{4}\/\d{1,2}\/\d{1,2}\//,
            /\/\d{4}\/\d{1,2}\//,
            /\/\d{4}-\d{2}-\d{2}/,
            /\/\d{8}\//,
            /\/(news|article|story|stories|post|posts|breaking|headlines?)\//i,
            /\/(world|politics|business|economy|sports?|entertainment|health|science|tech(nology)?|opinion|editorial)\//i,
            /\/(local|national|international|global)\//i,
            /\/(analysis|investigation|exclusive|feature|features)\//i,
            /\/[a-z]+-[a-z]+-[a-z]+(-[a-z]+){2,}/i,
            /-\d{5,}/,
            /\/[a-f0-9]{8,}/i,
        ];

        const hasNewsIndicator = newsIndicatorPatterns.some(
            (pattern) => pattern.test(pathname) || pattern.test(fullUrl)
        );

        if (hasNewsIndicator) return true;

        // Check for news-related terms in domain name
        const newsyDomainPatterns = [
            /news/i,
            /times/i,
            /post/i,
            /herald/i,
            /tribune/i,
            /journal/i,
            /gazette/i,
            /chronicle/i,
            /daily/i,
            /report(er)?/i,
            /press/i,
            /wire/i,
            /today/i,
        ];

        const hasNewsyDomain = newsyDomainPatterns.some((pattern) =>
            pattern.test(hostname)
        );

        if (hasNewsyDomain) {
            const pathParts = pathname.split("/").filter((p) => p.length > 0);
            return pathParts.length >= 2;
        }

        // Default: require strong signals
        const pathParts = pathname.split("/").filter((p) => p.length > 0);
        const hasArticleLikePath = pathParts.length >= 3 ||
            (pathParts.length >= 2 && pathParts.some(p => p.length > 20));

        return hasArticleLikePath;
    } catch (error) {
        return false;
    }
}

/**
 * Get cached result for a URL from local storage
 * Checks both cache key formats for compatibility with popup
 * @param {string} url - The URL to check
 * @returns {Object|null} Cached result or null
 */
async function getCachedResult(url) {
    try {
        // Check both cache key formats (popup uses 'analysis_${url}', background uses 'url')
        const cacheKey = `analysis_${url}`;
        const result = await chrome.storage.local.get([url, cacheKey]);

        // Check popup-style cache first (analysis_${url})
        if (result[cacheKey]) {
            const cached = result[cacheKey];
            // Popup stores full analysis data with propaganda_result
            if (cached.propaganda_result?.propaganda_probability !== undefined) {
                return {
                    propagandaProbability: cached.propaganda_result.propaganda_probability,
                    timestamp: Date.now() // Popup cache doesn't have timestamp, assume fresh
                };
            }
        }

        // Fall back to background-style cache (url)
        if (result[url]) {
            const cached = result[url];
            // Check if cache is still valid (24 hours)
            const now = Date.now();
            if (cached.timestamp && (now - cached.timestamp) < 24 * 60 * 60 * 1000) {
                return cached;
            }
        }
        return null;
    } catch (error) {
        console.error("Error getting cached result:", error);
        return null;
    }
}

/**
 * Save result to local storage cache
 * @param {string} url - The URL
 * @param {number} propagandaProbability - The propaganda probability (0-1)
 */
async function cacheResult(url, propagandaProbability) {
    try {
        await chrome.storage.local.set({
            [url]: {
                propagandaProbability,
                timestamp: Date.now()
            }
        });
    } catch (error) {
        console.error("Error caching result:", error);
    }
}

/**
 * Check backend for cached results and update badge
 * @param {string} url - The URL to check
 * @param {number} tabId - The tab ID
 */
async function checkAndUpdateBadge(url, tabId) {
    if (!isLikelyNewsUrl(url)) {
        await clearBadge(tabId);
        return;
    }

    // First check local cache
    const localCached = await getCachedResult(url);
    if (localCached && localCached.propagandaProbability !== undefined) {
        await setBadgeForPropaganda(localCached.propagandaProbability, tabId);
        return;
    }

    // Check backend cache
    try {
        const response = await fetch(`${API_URL}/database/getByURL/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        if (response.ok) {
            const data = await response.json();
            if (data && data.propaganda_result && data.propaganda_result.propaganda_probability !== undefined) {
                const propagandaProbability = data.propaganda_result.propaganda_probability;
                await setBadgeForPropaganda(propagandaProbability, tabId);
                // Cache locally for faster access
                await cacheResult(url, propagandaProbability);
            } else {
                // Article exists but no propaganda result yet - clear badge
                await clearBadge(tabId);
            }
        } else {
            // Not cached in backend - clear badge
            await clearBadge(tabId);
        }
    } catch (error) {
        // Backend not available or error - clear badge silently
        console.log("Could not check backend cache:", error.message);
        await clearBadge(tabId);
    }
}

// =============================================================================
// Context Menu Visibility
// =============================================================================

/**
 * Update context menu visibility based on whether the URL is a news site and toggle setting
 * @param {string} url - The current tab URL
 */
async function updateContextMenuVisibility(url) {
    try {
        const isNewsUrl = isLikelyNewsUrl(url);
        const { contextMenuEnabled } = await chrome.storage.sync.get('contextMenuEnabled');

        // Show context menu only if it's a news URL AND the toggle is enabled
        const shouldShow = isNewsUrl && (contextMenuEnabled !== false);

        await chrome.contextMenus.update("factcheck-selection", {
            visible: shouldShow
        });
    } catch (error) {
        console.error("Error updating context menu visibility:", error);
    }
}

// =============================================================================
// Storage Change Listener
// =============================================================================

// Listen for changes to context menu toggle setting
chrome.storage.onChanged.addListener(async (changes, areaName) => {
    if (areaName === 'sync' && changes.contextMenuEnabled) {
        // Update context menu visibility when toggle changes
        try {
            const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
            if (tab && tab.url) {
                await updateContextMenuVisibility(tab.url);
            }
        } catch (error) {
            console.error("Error updating context menu on toggle change:", error);
        }
    }
});

// =============================================================================
// Tab Event Listeners
// =============================================================================

// Gets the tab URL when you switch tabs
chrome.tabs.onActivated.addListener(async function(activeInfo) {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        tabUrl = tab.url;
        await checkAndUpdateBadge(tab.url, activeInfo.tabId);
        await updateContextMenuVisibility(tab.url);
    } catch (error) {
        console.error("Error on tab activation:", error);
    }
});

// Gets the tab URL when you go to a new link in the same tab
chrome.tabs.onUpdated.addListener(async function(tabId, changeInfo, tab) {
    // Only process when the URL changes or the page completes loading
    if (changeInfo.status === 'complete' || changeInfo.url) {
        try {
            const [activeTab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
            if (activeTab && activeTab.id === tabId) {
                tabUrl = tab.url;
                await checkAndUpdateBadge(tab.url, tabId);
                await updateContextMenuVisibility(tab.url);
            }
        } catch (error) {
            console.error("Error on tab update:", error);
        }
    }
});

// =============================================================================
// Message Handlers
// =============================================================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Handler for getting tab URL - always query fresh to handle service worker restarts
    if (message.action === 'getTabUrl') {
        (async () => {
            try {
                const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
                sendResponse({ tabUrl: tab?.url || null });
            } catch (error) {
                console.error("Error getting tab URL:", error);
                sendResponse({ tabUrl: null });
            }
        })();
        return true; // Keep message channel open for async response
    }

    // Handler for when analysis starts
    if (message.action === 'analysisStarted') {
        (async () => {
            try {
                const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
                if (tab) {
                    await setLoadingBadge(tab.id);
                }
                sendResponse({ success: true });
            } catch (error) {
                console.error("Error setting loading badge:", error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Keep message channel open for async response
    }

    // Handler for when propaganda result is received
    if (message.action === 'propagandaResultReceived') {
        (async () => {
            try {
                const { propagandaProbability, url } = message;
                const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
                if (tab) {
                    await setBadgeForPropaganda(propagandaProbability, tab.id);
                    // Cache the result
                    if (url) {
                        await cacheResult(url, propagandaProbability);
                    }
                }
                sendResponse({ success: true });
            } catch (error) {
                console.error("Error setting propaganda badge:", error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    }

    // Handler to clear badge
    if (message.action === 'clearBadge') {
        (async () => {
            try {
                const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
                if (tab) {
                    await clearBadge(tab.id);
                }
                sendResponse({ success: true });
            } catch (error) {
                console.error("Error clearing badge:", error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    }

    // Handler to open side panel
    if (message.action === 'openSidePanel') {
        (async () => {
            try {
                const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
                if (tab) {
                    await chrome.sidePanel.open({ windowId: tab.windowId });
                }
                sendResponse({ success: true });
            } catch (error) {
                console.error("Error opening side panel:", error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    }

    // Handler to get analysis data for popup
    if (message.action === 'getAnalysisData') {
        (async () => {
            try {
                const { url } = message;
                const response = await fetch(`${API_URL}/database/getByURL/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                if (response.ok) {
                    const data = await response.json();
                    sendResponse({ success: true, data });
                } else {
                    sendResponse({ success: false, data: null });
                }
            } catch (error) {
                console.error("Error getting analysis data:", error);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    }

    return false;
});
