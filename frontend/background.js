// API configuration
const API_URL = "http://localhost:8010";

// Open the side panel
chrome.sidePanel.setOptions({
    path: "index.html",
});

// Initialize extension on install
chrome.runtime.onInstalled.addListener(() => {
    // Don't auto-open side panel on click (we use popup now)
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });

    // Create context menu for fact-checking
    chrome.contextMenus.create({
        id: "factcheck-selection",
        title: "Fact-check this claim",
        contexts: ["selection"]
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
    if (info.menuItemId === "factcheck-selection") {
        // Check if context menu is enabled
        const { contextMenuEnabled } = await chrome.storage.sync.get('contextMenuEnabled');
        if (!contextMenuEnabled) return;

        const selectedText = info.selectionText;
        if (selectedText) {
            // Store the selected text for fact-checking
            await chrome.storage.local.set({ factcheckText: selectedText });
            // Open side panel with fact-check mode
            chrome.sidePanel.open({ windowId: tab.windowId });
        }
    }
});

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
 * @param {string} url - The URL to check
 * @returns {boolean} True if likely a news article
 */
function isLikelyNewsUrl(url) {
    if (!url) return false;

    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname.toLowerCase();
        const pathname = urlObj.pathname.toLowerCase();

        // Skip common non-news URLs
        const skipPatterns = [
            /^chrome:\/\//,
            /^chrome-extension:\/\//,
            /^about:/,
            /^file:/,
            /^moz-extension:/,
            /^edge:/,
        ];

        for (const pattern of skipPatterns) {
            if (pattern.test(url)) return false;
        }

        // Skip common non-article pages
        const nonArticlePatterns = [
            /\/(login|signup|register|account|cart|checkout|search)\/?$/i,
            /\/(category|categories|tag|tags|archive)\/?$/i,
            /^\/?$/,
            /\/?(index|home|about|contact|privacy|terms)\/?$/i,
        ];

        for (const pattern of nonArticlePatterns) {
            if (pattern.test(pathname)) return false;
        }

        // Check for common news site indicators
        const newsIndicators = [
            /\/article\//i,
            /\/news\//i,
            /\/story\//i,
            /\/\d{4}\/\d{2}\//,  // Date patterns like /2024/01/
            /\/(politics|business|tech|sports|entertainment|world|opinion)\//i,
        ];

        // Check if pathname has enough depth (likely an article)
        const pathParts = pathname.split('/').filter(p => p.length > 0);
        const hasDepth = pathParts.length >= 2;

        // Check for article-like patterns
        const hasNewsIndicator = newsIndicators.some(pattern => pattern.test(pathname));

        return hasDepth || hasNewsIndicator;
    } catch (error) {
        return false;
    }
}

/**
 * Get cached result for a URL from local storage
 * @param {string} url - The URL to check
 * @returns {Object|null} Cached result or null
 */
async function getCachedResult(url) {
    try {
        const result = await chrome.storage.local.get(url);
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
// Tab Event Listeners
// =============================================================================

// Gets the tab URL when you switch tabs
chrome.tabs.onActivated.addListener(async function(activeInfo) {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        tabUrl = tab.url;
        await checkAndUpdateBadge(tab.url, activeInfo.tabId);
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
    // Existing handler for getting tab URL
    if (message.action === 'getTabUrl') {
        sendResponse({ tabUrl });
        return true;
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
