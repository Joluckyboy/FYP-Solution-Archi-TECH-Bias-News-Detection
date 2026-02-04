import { useEffect } from 'react'
import './index.css'
import { AppRouter } from './router/AppRouter'

function App() {
  // Check if we need to redirect to a specific article (from popup)
  useEffect(() => {
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.local.get(['openArticleId'], (result) => {
        if (result.openArticleId) {
          // Clear the stored ID
          chrome.storage.local.remove('openArticleId');
          // Redirect to results page
          window.location.hash = `#/results/${result.openArticleId}`;
        }
      });
    }
  }, []);

  return (
    <>
      <AppRouter />
    </>
  )
}

export default App;
