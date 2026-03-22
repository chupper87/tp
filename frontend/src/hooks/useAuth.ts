import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";

interface User {
  id: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  user: User;
}

export function useAuth() {
  const queryClient = useQueryClient();

  const {
    data: user,
    isLoading,
    error,
  } = useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<User>("/auth/me"),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginCredentials) =>
      api.post<LoginResponse>("/auth/login", credentials),
    onSuccess: (data) => {
      queryClient.setQueryData(["auth", "me"], data.user);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSuccess: () => {
      queryClient.setQueryData(["auth", "me"], null);
      queryClient.clear();
    },
  });

  const isAuthenticated = !!user;
  const isAdmin = user?.is_admin ?? false;

  return {
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    error: error as ApiError | null,
    login: loginMutation.mutateAsync,
    loginError: loginMutation.error as ApiError | null,
    isLoggingIn: loginMutation.isPending,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
  };
}
