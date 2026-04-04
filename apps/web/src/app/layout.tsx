import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { QueryProvider } from '@/lib/query/provider';
import { ToastContextProvider } from '@/components/ui/use-toast';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'BehaviorSense Console',
  description: 'User Behavior Stream Analytics Engine - Admin Console',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <QueryProvider>
          <ToastContextProvider>{children}</ToastContextProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
