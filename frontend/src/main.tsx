import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'antd/dist/antd.css'

console.log('Starting application...')

// Create a client with better error handling
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
})

// Initialize the app
const initializeApp = () => {
  const rootElement = document.getElementById('root')
  
  if (!rootElement) {
    throw new Error('Root element not found!')
  }

  const root = ReactDOM.createRoot(rootElement)
  
  root.render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>
  )
}

// Start the app with error handling
try {
  initializeApp()
} catch (error) {
  console.error('Failed to initialize app:', error)
  // You might want to show a user-friendly error message here
  document.body.innerHTML = `
    <div style="color: red; padding: 20px; text-align: center;">
      <h1>Application Error</h1>
      <p>Failed to initialize the application. Please refresh the page or contact support.</p>
    </div>
  `
}
