export const MUSCLE_GROUPS = [
  "chest",
  "back",
  "shoulders",
  "arms",
  "core",
  "glutes",
  "thighs",
  "calves",
] as const;
export type MuscleGroup = (typeof MUSCLE_GROUPS)[number];

export const MOVEMENT_PATTERNS = [
  "horizontal_push",
  "vertical_push",
  "horizontal_pull",
  "vertical_pull",
  "squat",
  "hip_hinge",
  "lunge",
  "hip_extension",
  "knee_flexion",
  "knee_extension",
  "elbow_flexion",
  "elbow_extension",
  "shoulder_abduction",
  "shoulder_horizontal_abduction",
  "chest_fly",
  "core_flexion",
  "core_anti_extension",
  "calf_raise",
] as const;
export type MovementPattern = (typeof MOVEMENT_PATTERNS)[number];

export type MuscleRole = "primary" | "secondary" | "stabilizer";

export type EquipmentCategory = "free_weights" | "station" | "cable" | "machine";

export type ExerciseType = "compound" | "isolation";

export type ExerciseSort = "name_en" | "name_pl" | "group";

export type Muscle = {
  id: number;
  code: string;
  name_pl: string;
  name_en: string;
  muscle_group: MuscleGroup;
  is_volume_target: boolean;
};

export type Equipment = {
  id: number;
  code: string;
  name_en: string;
  name_pl: string;
  category: EquipmentCategory;
};

export type ExerciseSummary = {
  id: number;
  code: string;
  name_en: string;
  name_pl: string;
  main_group: MuscleGroup;
  movement_pattern: MovementPattern;
  is_compound: boolean;
  is_unilateral: boolean;
  image_url: string | null;
  equipment: Equipment[];
};

export type MuscleShare = {
  muscle: Muscle;
  role: MuscleRole;
  weight: number;
  share_pct: number;
};

export type ExerciseDetail = ExerciseSummary & {
  fatigue_cost: number;
  complexity: number;
  default_tempo: string | null;
  instructions_pl: string | null;
  instructions_en: string | null;
  muscles: MuscleShare[];
};

/** Filters that narrow the per-group counts (everything except the group itself). */
export type ExerciseCountQuery = {
  search?: string;
  pattern?: MovementPattern;
  type?: ExerciseType;
  availableWith?: number[];
};

export type ExerciseQuery = ExerciseCountQuery & {
  page: number;
  sort: ExerciseSort;
  muscleGroup?: MuscleGroup;
};
