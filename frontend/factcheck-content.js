// Fact-check content script
// Displays fact-check results in a tooltip near the selected text

(function() {
    // Prevent multiple injections
    if (window.__factcheckContentScriptLoaded) return;
    window.__factcheckContentScriptLoaded = true;

    const TOOLTIP_ID = 'checkmate-factcheck-tooltip';

    // Store selection position for tooltip placement
    let lastSelectionRect = null;

    // Capture selection position before context menu appears
    document.addEventListener('mouseup', (e) => {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length > 0) {
            const range = selection.getRangeAt(0);
            lastSelectionRect = range.getBoundingClientRect();
        }
    });

    // Also capture on contextmenu event
    document.addEventListener('contextmenu', (e) => {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length > 0) {
            const range = selection.getRangeAt(0);
            lastSelectionRect = range.getBoundingClientRect();
        }
    });

    // Create and inject styles
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

            #${TOOLTIP_ID} * {
                box-sizing: border-box;
            }

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

            .checkmate-header-title img {
                width: 20px;
                height: 20px;
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

            .checkmate-content {
                padding: 16px;
            }

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

            @keyframes checkmate-spin {
                to { transform: rotate(360deg); }
            }

            .checkmate-loading-text {
                color: #6b7280;
                font-size: 13px;
            }

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

            .checkmate-verdict-factual {
                background: #dcfce7;
                color: #166534;
            }

            .checkmate-verdict-unfactual {
                background: #fee2e2;
                color: #991b1b;
            }

            .checkmate-verdict-undetermined {
                background: #fef3c7;
                color: #92400e;
            }

            .checkmate-explanation {
                font-size: 13px;
                color: #4b5563;
                margin-bottom: 12px;
            }

            .checkmate-citations {
                border-top: 1px solid #e5e7eb;
                padding-top: 12px;
            }

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

            .checkmate-citation-link:hover {
                text-decoration: underline;
            }

            .checkmate-error {
                color: #dc2626;
                text-align: center;
                padding: 16px;
            }

            .checkmate-error-icon {
                font-size: 24px;
                margin-bottom: 8px;
            }
        `;
        document.head.appendChild(styles);
    }

    // Get verdict class and icon
    function getVerdictInfo(correctness) {
        const normalized = (correctness || '').toLowerCase().trim();

        if (normalized === 'factual' || normalized.includes('factual') && !normalized.includes('unfactual')) {
            return { class: 'checkmate-verdict-factual', icon: '\u2705', label: 'Factual' };
        } else if (normalized === 'unfactual' || normalized.includes('unfactual') || normalized.includes('false')) {
            return { class: 'checkmate-verdict-unfactual', icon: '\u274C', label: 'Unfactual' };
        } else {
            return { class: 'checkmate-verdict-undetermined', icon: '\u2753', label: 'Cannot Be Determined' };
        }
    }

    // Create tooltip element
    function createTooltip() {
        removeTooltip(); // Remove any existing tooltip
        injectStyles();

        const tooltip = document.createElement('div');
        tooltip.id = TOOLTIP_ID;
        document.body.appendChild(tooltip);
        return tooltip;
    }

    // Remove tooltip
    function removeTooltip() {
        const existing = document.getElementById(TOOLTIP_ID);
        if (existing) {
            existing.remove();
        }
    }

    // Position tooltip near selection
    function positionTooltip(tooltip) {
        if (!lastSelectionRect) {
            // Fallback: center on screen
            tooltip.style.left = '50%';
            tooltip.style.top = '20%';
            tooltip.style.transform = 'translateX(-50%)';
            return;
        }

        const rect = lastSelectionRect;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const tooltipRect = tooltip.getBoundingClientRect();

        // Calculate position below the selection
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        let top = rect.bottom + 10;

        // Adjust if tooltip goes off screen horizontally
        if (left < 10) left = 10;
        if (left + tooltipRect.width > viewportWidth - 10) {
            left = viewportWidth - tooltipRect.width - 10;
        }

        // If tooltip would go below viewport, show above selection
        if (top + tooltipRect.height > viewportHeight - 10) {
            top = rect.top - tooltipRect.height - 10;
        }

        // Ensure tooltip stays in viewport
        if (top < 10) top = 10;

        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    // Get extension icon URL
    function getIconUrl() {
        try {
            return chrome.runtime.getURL('checkmate.png');
        } catch {
            return '';
        }
    }

    // Show loading state
    function showLoading(claim) {
        const tooltip = createTooltip();
        const iconUrl = getIconUrl();

        tooltip.innerHTML = `
            <div class="checkmate-header">
                <div class="checkmate-header-title">
                    ${iconUrl ? `<img src="${iconUrl}" alt="Checkmate">` : ''}
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

        // Position after content is rendered
        requestAnimationFrame(() => positionTooltip(tooltip));
    }

    // Show results
    function showResults(data) {
        const tooltip = document.getElementById(TOOLTIP_ID) || createTooltip();
        const iconUrl = getIconUrl();
        const verdictInfo = getVerdictInfo(data.correctness);

        // Build citations HTML
        let citationsHtml = '';
        if (data.citations && data.citations.length > 0) {
            const citationLinks = data.citations.map((citation, index) => {
                const url = typeof citation === 'string' ? citation : citation.url || citation.source || '';
                if (!url) return '';

                // Try to extract domain for display
                let displayText = url;
                try {
                    const urlObj = new URL(url);
                    displayText = urlObj.hostname.replace('www.', '');
                } catch {
                    displayText = url.slice(0, 50) + (url.length > 50 ? '...' : '');
                }

                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="checkmate-citation-link">[${index + 1}] ${displayText}</a>`;
            }).filter(Boolean).join('');

            if (citationLinks) {
                citationsHtml = `
                    <div class="checkmate-citations">
                        <div class="checkmate-citations-title">Sources</div>
                        ${citationLinks}
                    </div>
                `;
            }
        }

        tooltip.innerHTML = `
            <div class="checkmate-header">
                <div class="checkmate-header-title">
                    ${iconUrl ? `<img src="${iconUrl}" alt="Checkmate">` : ''}
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
                <div class="checkmate-explanation">
                    ${escapeHtml(data.explanation || 'No explanation available.')}
                </div>
                ${citationsHtml}
            </div>
        `;

        tooltip.querySelector('.checkmate-close-btn').addEventListener('click', removeTooltip);

        // Position after content is rendered
        requestAnimationFrame(() => positionTooltip(tooltip));
    }

    // Show error
    function showError(message) {
        const tooltip = document.getElementById(TOOLTIP_ID) || createTooltip();
        const iconUrl = getIconUrl();

        tooltip.innerHTML = `
            <div class="checkmate-header">
                <div class="checkmate-header-title">
                    ${iconUrl ? `<img src="${iconUrl}" alt="Checkmate">` : ''}
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

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === 'factcheckLoading') {
            showLoading(message.claim);
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

    // Close tooltip when clicking outside
    document.addEventListener('click', (e) => {
        const tooltip = document.getElementById(TOOLTIP_ID);
        if (tooltip && !tooltip.contains(e.target)) {
            removeTooltip();
        }
    });

    // Close tooltip on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            removeTooltip();
        }
    });

    console.log('[Checkmate] Fact-check content script loaded');
})();
