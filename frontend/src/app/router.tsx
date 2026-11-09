import { createBrowserRouter, Navigate } from "react-router";

import { GuestOnly } from "@/features/auth/components/GuestOnly";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { RegisterPage } from "@/features/auth/pages/RegisterPage";
import { CatalogLayout } from "@/features/catalog/CatalogLayout";
import { EquipmentPage } from "@/features/catalog/equipment/pages/EquipmentPage.tsx";
import { ExerciseDetailDialog } from "@/features/catalog/exercises/pages/ExerciseDetailDialog.tsx";
import { ExercisesPage } from "@/features/catalog/exercises/pages/ExercisesPage.tsx";
import { MusclesPage } from "@/features/catalog/muscles/pages/MusclesPage.tsx";
import { PlanPage } from "@/features/plan/pages/PlanPage";
import { StartPage } from "@/features/plan/pages/StartPage";
import { ProfilePage } from "@/features/profile/pages/ProfilePage";
import { WorkoutPage } from "@/features/workout/pages/WorkoutPage";
import { AppLayout } from "@/layouts/AppLayout";
import { AuthLayout } from "@/layouts/AuthLayout";
import { NotFoundPage } from "@/pages/NotFoundPage";

export const router = createBrowserRouter([
  // Public
  {
    element: <AuthLayout />,
    children: [
      {
        element: <GuestOnly />,
        children: [
          { path: "/login", element: <LoginPage /> },
          { path: "/register", element: <RegisterPage /> },
        ],
      },
    ],
  },
  // Signed in
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <StartPage /> },
          { path: "/plans", element: <PlanPage /> },
          {
            path: "/catalog",
            element: <CatalogLayout />,
            children: [
              { index: true, element: <Navigate to="exercises" replace /> },
              {
                path: "exercises",
                element: <ExercisesPage />,
                children: [{ path: ":exerciseId", element: <ExerciseDetailDialog /> }],
              },
              { path: "muscles", element: <MusclesPage /> },
              { path: "equipment", element: <EquipmentPage /> },
            ],
          },
          { path: "/workout", element: <WorkoutPage /> },
          { path: "/profile", element: <ProfilePage /> },
        ],
      },
      { path: "/workout/:sessionId", element: <WorkoutPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
