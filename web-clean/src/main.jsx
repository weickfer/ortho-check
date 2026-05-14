import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Map } from './components/map.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Map />
  </StrictMode>,
)
