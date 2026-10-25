import "../styles/globals.css";

export const metadata = {
  title: 'StrandedPool | Travel recovery',
  description: 'Plan a practical next step when travel plans are disrupted.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
