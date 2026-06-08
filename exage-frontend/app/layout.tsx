import type { Metadata } from 'next'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'ExAge — Expose what you don\'t know',
  description: 'An AI-powered diagnostic learning tool that reveals hidden gaps in your understanding.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
