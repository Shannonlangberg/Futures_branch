import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Futures Pulse Passport',
  description: 'Discipleship and leadership tracking platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{
        margin: 0,
        padding: 0,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        backgroundColor: '#0f172a',
        color: '#ffffff'
      }}>
        {children}
      </body>
    </html>
  );
}
