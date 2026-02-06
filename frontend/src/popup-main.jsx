import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import PopupPage from './pages/PopupPage'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <PopupPage />
  </StrictMode>,
)
