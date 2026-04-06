import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Note: Token stored in localStorage for demo purposes
// In production, use httpOnly cookies for better XSS protection

export type UserRole = 'admin' | 'analyst' | 'viewer';

export interface User {
  userId: string;
  username: string;
  email?: string;
  avatar?: string;
  roles: string[];
  role?: UserRole; // Primary role for role-based filtering
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  _hydrated: boolean;
  setAuth: (token: string, user: User) => void;
  login: (user: User, token: string) => void; // Alias for setAuth
  logout: () => void;
  hasRole: (role: string) => boolean;
  updateUser: (userData: Partial<User>) => void;
  setHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      _hydrated: false,
      setAuth: (token, user) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', token);
        }
        set({ token, user, isAuthenticated: true, _hydrated: true });
      },
      login: (user, token) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', token);
        }
        set({ token, user, isAuthenticated: true, _hydrated: true });
      },
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
        }
        set({ token: null, user: null, isAuthenticated: false, _hydrated: true });
      },
      hasRole: (role) => {
        const { user } = get();
        return user?.roles.includes(role) ?? false;
      },
      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }));
      },
      setHydrated: (state) => set({ _hydrated: state }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // After rehydration, set authenticated based on token presence
          const isAuthenticated = !!state.token && !!state.user;
          useAuthStore.setState({
            isAuthenticated,
            _hydrated: true
          });
        } else {
          // Even if state is null, mark as hydrated
          useAuthStore.setState({ _hydrated: true });
        }
      },
    }
  )
);
