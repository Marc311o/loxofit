import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";

import i18n from "@/i18n";
import {
  api,
  ApiError,
  errorMessage,
  getFieldErrors,
  refreshSession,
  type TokenResponse,
} from "@/lib/api";
import { session } from "@/lib/session";
import { toast } from "@/lib/toast";

export type User = {
  id: string;
  email: string;
  display_name: string | null;
  role: "user" | "admin";
  created_at: string;
};

export type LoginRequest = { email: string; password: string };
export type RegisterRequest = LoginRequest & { display_name?: string };

export const currentUserKey = ["auth", "me"] as const;

/** The signed-in user. On a cold start it first restores the session from the refresh cookie. */
export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserKey,
    queryFn: async () => {
      if (session.getAccessToken() === null && !(await refreshSession())) {
        throw new ApiError(401, "NOT_AUTHENTICATED", "Not signed in");
      }
      return api.get<User>("/auth/me");
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

function login({ email, password }: LoginRequest) {
  return api.postForm<TokenResponse>("/auth/login", {
    username: email,
    password,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation<TokenResponse, ApiError, LoginRequest>({
    mutationFn: login,
    onSuccess: (tokens) => {
      session.setAccessToken(tokens.access_token);
      return queryClient.resetQueries({ queryKey: currentUserKey });
    },
  });
}

/** Registers and signs the new user in straight away. */
export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation<TokenResponse, ApiError, RegisterRequest>({
    mutationFn: async (data) => {
      await api.post<User>("/auth/register", data);
      return login(data);
    },
    onSuccess: (tokens) => {
      session.setAccessToken(tokens.access_token);
      toast.success(i18n.t("auth:register.welcome"));
      return queryClient.resetQueries({ queryKey: currentUserKey });
    },
    onError: (error) => {
      const fieldErrors = getFieldErrors(error);
      if (error.code !== "EMAIL_TAKEN" && Object.keys(fieldErrors).length === 0) {
        toast.error(errorMessage(error));
      }
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSettled: () => {
      session.clear();
      queryClient.clear();
      navigate("/login", { replace: true });
    },
  });
}
