import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import 'bootstrap/dist/css/bootstrap.min.css'

console.log('Starting application...')

const rootElement = document.getElementById('root')
console.log('Root element:', rootElement)

if (!rootElement) {
  console.error('Root element not found!')
} else {
  try {
    const root = ReactDOM.createRoot(rootElement)
    console.log('Root created successfully')
    
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    )
    console.log('App rendered successfully')
  } catch (error) {
    console.error('Error rendering app:', error)
  }
}
