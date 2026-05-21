import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ARES-X | Cyber Battlefield Platform',
  description: 'Advanced cyber battlefield visualization and attack path analysis platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-abyss text-text-primary font-sans min-h-screen">
        {children}
      </body>
    </html>
  );
}
