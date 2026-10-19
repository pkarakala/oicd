import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as RadixTooltip from '@radix-ui/react-tooltip'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './shell/App'

const client = new QueryClient({ defaultOptions: { queries: { refetchOnWindowFocus: false } } })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={client}>
      <RadixTooltip.Provider delayDuration={350} skipDelayDuration={150}>
        <App />
      </RadixTooltip.Provider>
    </QueryClientProvider>
  </StrictMode>,
)
