import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";

export type ExperienceLevel = "beginner" | "intermediate" | "advanced";

export type Profile = {
  experience: ExperienceLevel;
  days_per_week: number;
  max_session_minutes: number;
  /** ISO weekdays, 1 = Monday; null - no preference. */
  preferred_weekdays: number[] | null;
  weight_kg: number | null;
  updated_at: string;
};

export type ProfileWrite = Omit<Profile, "updated_at">;

export const profileKey = ["users", "me", "profile"] as const;

/** The training profile, or `null` when the user has not filled it in yet (404 PROFILE_NOT_FOUND). */
export function useMyProfile() {
  return useQuery({
    queryKey: profileKey,
    queryFn: async () => {
      try {
        return await api.get<Profile>("/users/me/profile");
      } catch (error) {
        if (error instanceof ApiError && error.code === "PROFILE_NOT_FOUND") return null;
        throw error;
      }
    },
  });
}

/** Creates or replaces the profile; the response becomes the cached value. */
export function useSaveProfile() {
  const queryClient = useQueryClient();
  return useMutation<Profile, ApiError, ProfileWrite>({
    mutationFn: (data) => api.put<Profile>("/users/me/profile", data),
    onSuccess: (profile) => queryClient.setQueryData(profileKey, profile),
  });
}