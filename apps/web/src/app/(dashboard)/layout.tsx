import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { ProtectedRoute } from '@/lib/auth/protected';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToastContextProvider } from '@/components/ui/use-toast';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <ToastContextProvider>
        <TooltipProvider>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-auto bg-muted/30 p-6">
                {children}
              </main>
            </div>
          </div>
        </TooltipProvider>
      </ToastContextProvider>
    </ProtectedRoute>
  );
}
