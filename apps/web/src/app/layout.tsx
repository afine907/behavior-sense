import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { QueryProvider } from '@/lib/query/provider';
import { ToastContextProvider } from '@/components/ui/use-toast';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'BehaviorSense - AI Agent Analytics',
  description: 'Real-time AI Agent behavior monitoring and analytics',
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        <QueryProvider>
          <ToastContextProvider>{children}</ToastContextProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
