import { useState } from "react";
import ArrowBackRounded from "@mui/icons-material/ArrowBackRounded";
import AutoAwesomeRounded from "@mui/icons-material/AutoAwesomeRounded";
import CheckCircleRounded from "@mui/icons-material/CheckCircleRounded";
import EditNoteRounded from "@mui/icons-material/EditNoteRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  InputAdornment,
  LinearProgress,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { FullScreenLoader } from "@/components/FullScreenLoader";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useSaveMyEquipment } from "@/features/catalog/equipment/api";
import { useMyProfile, useSaveProfile } from "../api";
import { EquipmentPicker } from "../components/EquipmentPicker";
import { ExperiencePicker } from "../components/ExperiencePicker";
import { TrainingFields } from "../components/TrainingFields";
import { EMPTY_PROFILE, type ProfileForm, toProfileWrite, weightError } from "../form";

const STEPS = ["about", "training", "equipment", "done"] as const;
type Step = (typeof STEPS)[number];

/**
 * First run after registration: who you are, how you train, what you have.
 * The profile is saved last - its existence marks the onboarding as finished.
 */
export function OnboardingPage() {
  const { t } = useTranslation("profile");
  const navigate = useNavigate();
  const profile = useMyProfile();
  const saveEquipment = useSaveMyEquipment();
  const saveProfile = useSaveProfile();

  const [step, setStep] = useState<Step>("about");
  const [form, setForm] = useState<ProfileForm>(EMPTY_PROFILE);
  const [equipment, setEquipment] = useState<ReadonlySet<number>>(new Set());
  const [tried, setTried] = useState(false);
  // Saving the profile ends the onboarding - from then on this page shows the last step.
  const [finishing, setFinishing] = useState(false);
  const saving = saveEquipment.isPending || saveProfile.isPending;

  if (profile.isPending) return <FullScreenLoader />;
  // Finished before (e.g. the back button after the last step) - nothing to do here.
  if (profile.data && !finishing) return <Navigate to="/" replace />;

  const index = STEPS.indexOf(step);
  const update = (change: Partial<ProfileForm>) => setForm((f) => ({ ...f, ...change }));

  const next = async () => {
    setTried(true);
    if (step === "about") {
      if (form.experience === null || weightError(form)) return;
      setTried(false);
      setStep("training");
    } else if (step === "training") {
      setTried(false);
      setStep("equipment");
    } else if (step === "equipment") {
      if (equipment.size === 0) return;
      setFinishing(true);
      try {
        await saveEquipment.mutateAsync([...equipment]);
        await saveProfile.mutateAsync(toProfileWrite(form));
        setStep("done");
      } catch {
        setFinishing(false); // the error is shown as a toast
      }
    }
  };

  return (
    <Box sx={{ minHeight: "100dvh", bgcolor: "background.default", px: 2, py: { xs: 3, sm: 5 } }}>
      {/* wider for the equipment tiles */}
      <Stack spacing={3} sx={{ maxWidth: step === "equipment" ? 760 : 560, mx: "auto" }}>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
          <Logo size={32} />
          <LanguageSwitcher />
        </Stack>

        {step !== "done" && (
          <Stack spacing={1}>
            <Typography
              variant="overline"
              color="text.secondary"
              aria-live="polite"
              sx={{ lineHeight: 1.5 }}
            >
              {t("onboarding.progress", { step: index + 1, total: STEPS.length - 1 })}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={((index + 1) / (STEPS.length - 1)) * 100}
              aria-label={t("onboarding.progressLabel")}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Stack>
        )}

        <Card sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          {step === "done" ? (
            <Done
              onGenerate={() => navigate("/plans/generate")}
              onManual={() => navigate("/plans")}
            />
          ) : (
            <Stack
              component="form"
              spacing={3}
              noValidate
              onSubmit={(event) => {
                event.preventDefault();
                void next();
              }}
            >
              <Stack spacing={0.5}>
                <Typography variant="h2" component="h1">
                  {t(`onboarding.${step}.title`)}
                </Typography>
                <Typography color="text.secondary">{t(`onboarding.${step}.subtitle`)}</Typography>
              </Stack>

              {step === "about" && (
                <Stack spacing={3}>
                  <ExperiencePicker
                    value={form.experience}
                    onChange={(experience) => update({ experience })}
                    error={tried && form.experience === null}
                  />
                  <TextField
                    label={t("fields.weight")}
                    value={form.weight}
                    onChange={(e) => update({ weight: e.target.value })}
                    error={tried && weightError(form)}
                    helperText={
                      tried && weightError(form)
                        ? t("fields.weightInvalid")
                        : t("fields.weightHint")
                    }
                    slotProps={{
                      htmlInput: { inputMode: "decimal" },
                      input: { endAdornment: <InputAdornment position="end">kg</InputAdornment> },
                      inputLabel: { shrink: true }, // the label stays clear of "kg"
                    }}
                    sx={{ maxWidth: 260 }}
                  />
                </Stack>
              )}

              {step === "training" && <TrainingFields form={form} onChange={update} />}

              {step === "equipment" && (
                <Stack spacing={2}>
                  <EquipmentPicker selected={equipment} onChange={setEquipment} />
                  {tried && equipment.size === 0 && (
                    <Alert severity="warning">{t("equipment.required")}</Alert>
                  )}
                </Stack>
              )}

              <Stack direction="row" spacing={1.5} sx={{ justifyContent: "space-between" }}>
                {index > 0 ? (
                  <Button
                    startIcon={<ArrowBackRounded />}
                    onClick={() => {
                      setTried(false);
                      setStep(STEPS[index - 1]);
                    }}
                    disabled={saving}
                  >
                    {t("onboarding.back")}
                  </Button>
                ) : (
                  <span />
                )}
                <Button type="submit" variant="contained" size="large" loading={saving}>
                  {step === "equipment" ? t("onboarding.finish") : t("onboarding.next")}
                </Button>
              </Stack>
            </Stack>
          )}
        </Card>
      </Stack>
    </Box>
  );
}

function Done({ onGenerate, onManual }: { onGenerate: () => void; onManual: () => void }) {
  const { t } = useTranslation("profile");
  const navigate = useNavigate();
  return (
    <Stack spacing={3} sx={{ alignItems: "flex-start" }}>
      <CheckCircleRounded color="primary" sx={{ fontSize: 48 }} />
      <Stack spacing={0.5}>
        <Typography variant="h2" component="h1">
          {t("onboarding.done.title")}
        </Typography>
        <Typography color="text.secondary">{t("onboarding.done.subtitle")}</Typography>
      </Stack>
      <Stack spacing={1.5} sx={{ width: "100%" }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<AutoAwesomeRounded />}
          onClick={onGenerate}
        >
          {t("onboarding.done.generate")}
        </Button>
        <Button variant="outlined" size="large" startIcon={<EditNoteRounded />} onClick={onManual}>
          {t("onboarding.done.manual")}
        </Button>
        <Button onClick={() => navigate("/")}>{t("onboarding.done.later")}</Button>
      </Stack>
    </Stack>
  );
}
