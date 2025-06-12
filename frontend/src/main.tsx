import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'antd/dist/antd.css'

console.log('Starting application...')

const rootElement = document.getElementById('root')
console.log('Root element:', rootElement)

if (!rootElement) {
  console.error('Root element not found!')
} else {
  try {
    // Create a client
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          refetchOnWindowFocus: false,
          retry: 1,
        },
      },
    })

    const root = ReactDOM.createRoot(rootElement)
    console.log('Root created successfully')
    
    root.render(
      <React.StrictMode>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </React.StrictMode>
    )
    console.log('App rendered successfully')
  } catch (error) {
    console.error('Error rendering app:', error)
  }
}
