
// Open the side panel
chrome.sidePanel.setOptions({
    path: "index.html",  // Path to the content you want in the side panel
});

// Make it so that clicking on the extension icon opens the side panel
chrome.runtime.onInstalled.addListener(() => {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  });
// (async () => {
//     // see the note below on how to choose currentWindow or lastFocusedWindow
//     const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
//     console.log(tab.url);
// })();

console.log("Background script loaded");

// Gets the tab URL when you switch tabs
chrome.tabs.onActivated.addListener( function(activeInfo){
    (async () => {
        // see the note below on how to choose currentWindow or lastFocusedWindow
        const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
        // console.log(tab.id);
        tabUrl = tab.url;
        tabID = tab.id;
    })();
    
});

// Gets the tab URL when you go to a new link in the same tab
chrome.tabs.onUpdated.addListener( function(activeInfo){
    (async () => {
        // see the note below on how to choose currentWindow or lastFocusedWindow
        const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
        // console.log(tab.id);
        tabUrl = tab.url;
        tabID = tab.id;
    })();
    
});

let tabUrl = null;
let tabID = null;

// Listen for messages from your React component and send back the tabUrl
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getTabUrl') {
        sendResponse({ tabUrl });
    }
});

