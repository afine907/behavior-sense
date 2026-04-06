'use client';

import { useMutation } from '@tanstack/react-query';
import { useAuthStore, type User } from '@/lib/stores/auth';
import { useRouter } from 'next/navigation';

interface LoginInput {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: User;
}

export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: async (input: LoginInput): Promise<LoginResponse> => {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      return response.json();
    },
    onSuccess: (data) => {
      setAuth(data.token, data.user);
      router.push('/');
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);

  return () => {
    logout();
    router.push('/login');
  };
}

export function useCurrentUser() {
  return useAuthStore((state) => state.user);
}

export function useIsAuthenticated() {
  return useAuthStore((state) => state.isAuthenticated);
}

export function useHasRole(role: string) {
  return useAuthStore((state) => state.hasRole(role));
}
