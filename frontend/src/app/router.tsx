import { createBrowserRouter, Navigate } from "react-router";
import { AuthLayout } from "../layouts/AuthLayout.tsx";
import { LoginPage } from "../features/auth/pages/LoginPage.tsx";
import { RegisterPage } from "../features/auth/pages/RegisterPage.tsx";
import { AppLayout } from "../layouts/AppLayout.tsx";
import { StartPage } from "../features/plan/pages/StartPage.tsx";
import { CatalogLayout } from "../features/catalog/CatalogLayout.tsx";
import { ExercisesPage } from "../features/catalog/pages/ExercisePage.tsx";
import { ExerciseDetailDialog } from "../features/catalog/pages/ExerciseDetailDialog.tsx";
import { MusclesPage } from "../features/catalog/pages/MusclesPage.tsx";
import { EquipmentPage } from "../features/catalog/pages/EquipmentPage.tsx";
import { ProfilePage } from "../features/profile/pages/ProfilePage.tsx";
import { PlanPage } from "../features/plan/pages/PlanPage.tsx";
import { WorkoutPage } from "../features/workout/pages/WorkoutPage.tsx";

export const router = createBrowserRouter([
  // Auth
  {
    element: <AuthLayout />,
    children: [
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
    ],
  },
  // App
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <StartPage /> },
      {
        path: "catalog",
        element: <CatalogLayout />,
        children: [
          { index: true, element: <Navigate to="exercises" replace /> },
          {
            path: "exercises",
            element: <ExercisesPage />,
            children: [
              { path: ":exerciseId", element: <ExerciseDetailDialog /> },
            ],
          },
          { path: "muscles", element: <MusclesPage /> },
          { path: "equipment", element: <EquipmentPage /> },
        ],
      },
      { path: "plan", element: <PlanPage /> },
      { path: "profile", element: <ProfilePage /> },
    ],
  },
  // Tracker
  { path: "workout/:sessionId", element: <WorkoutPage /> },
  { path: "*", element: <NotFoundPage /> },
]);
