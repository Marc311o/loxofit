import { useState } from "react";
import {
  Button,
  Card,
  Divider,
  InputAdornment,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { PageHeader } from "@/components/PageHeader";
import { useCurrentUser } from "@/features/auth/api";
import { useMyEquipment } from "@/features/catalog/equipment/api";
import { toast } from "@/lib/toast";
import { type Profile, useMyProfile, useSaveProfile } from "../api";
import { ChangePasswordDialog } from "../components/ChangePasswordDialog";
import { DeleteAccountDialog } from "../components/DeleteAccountDialog";
import { ExperiencePicker } from "../components/ExperiencePicker";
import { TrainingFields } from "../components/TrainingFields";
import { fromProfile, type ProfileForm, toProfileWrite, weightError } from "../form";

/** The training profile (the generator's defaults), equipment, account and language. */
export function ProfilePage() {
  const { t } = useTranslation("profile");
  const user = useCurrentUser();
  const profile = useMyProfile();
  const equipment = useMyEquipment();
  const [dialog, setDialog] = useState<"password" | "delete" | null>(null);

  return (
    <>
      <PageHeader title={t("page.title")} subtitle={user.data?.email} />
      <Stack spacing={2.5} sx={{ maxWidth: 720 }}>
        {profile.data ? (
          <TrainingProfileCard key={profile.data.updated_at} profile={profile.data} />
        ) : (
          <Skeleton variant="rounded" height={480} />
        )}

        <Section title={t("page.equipment")}>
          <Stack
            direction="row"
            sx={{ justifyContent: "space-between", alignItems: "center", gap: 2 }}
          >
            <Typography color="text.secondary">
              {equipment.data ? t("equipment.selected", { count: equipment.data.length }) : "…"}
            </Typography>
            <Button component={RouterLink} to="/catalog/equipment" variant="outlined">
              {t("page.editEquipment")}
            </Button>
          </Stack>
        </Section>

        <Section title={t("page.account")}>
          <Stack spacing={2} divider={<Divider flexItem />}>
            <Row label={t("account.email")} value={user.data?.email ?? "…"} />
            <Row
              label={t("account.password")}
              action={
                <Button variant="outlined" onClick={() => setDialog("password")}>
                  {t("account.changePassword")}
                </Button>
              }
            />
            <Row label={t("account.language")} action={<LanguageSwitcher />} />
            <Row
              label={t("account.deleteLabel")}
              hint={t("account.deleteHint")}
              action={
                <Button color="error" variant="outlined" onClick={() => setDialog("delete")}>
                  {t("account.delete")}
                </Button>
              }
            />
          </Stack>
        </Section>
      </Stack>

      {dialog === "password" && <ChangePasswordDialog onClose={() => setDialog(null)} />}
      {dialog === "delete" && <DeleteAccountDialog onClose={() => setDialog(null)} />}
    </>
  );
}

/** Mounted per saved version (`key`), so after saving the form starts from the new values. */
function TrainingProfileCard({ profile }: { profile: Profile }) {
  const { t } = useTranslation("profile");
  const save = useSaveProfile();
  const [form, setForm] = useState<ProfileForm>(() => fromProfile(profile));
  const update = (change: Partial<ProfileForm>) => setForm((f) => ({ ...f, ...change }));
  const dirty = JSON.stringify(form) !== JSON.stringify(fromProfile(profile));
  const invalidWeight = weightError(form);

  return (
    <Section title={t("page.training")} hint={t("page.trainingHint")}>
      <Stack
        component="form"
        spacing={3}
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          if (invalidWeight) return;
          save.mutate(toProfileWrite(form), { onSuccess: () => toast.success(t("page.saved")) });
        }}
      >
        <ExperiencePicker
          value={form.experience}
          onChange={(experience) => update({ experience })}
        />
        <TextField
          label={t("fields.weight")}
          value={form.weight}
          onChange={(e) => update({ weight: e.target.value })}
          error={invalidWeight}
          helperText={invalidWeight ? t("fields.weightInvalid") : t("fields.weightHint")}
          slotProps={{
            htmlInput: { inputMode: "decimal" },
            input: { endAdornment: <InputAdornment position="end">kg</InputAdornment> },
            inputLabel: { shrink: true }, // the label stays clear of "kg"
          }}
          sx={{ maxWidth: 260 }}
        />
        <TrainingFields form={form} onChange={update} />
        <Stack direction="row" spacing={1.5} sx={{ justifyContent: "flex-end" }}>
          <Button disabled={!dirty || save.isPending} onClick={() => setForm(fromProfile(profile))}>
            {t("actions.cancel")}
          </Button>
          <Button type="submit" variant="contained" disabled={!dirty} loading={save.isPending}>
            {t("actions.save")}
          </Button>
        </Stack>
      </Stack>
    </Section>
  );
}

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <Card component="section" aria-label={title} sx={{ p: { xs: 2, sm: 3 } }}>
      <Stack spacing={0.5} sx={{ mb: 2.5 }}>
        <Typography variant="h3" component="h2">
          {title}
        </Typography>
        {hint && (
          <Typography variant="body2" color="text.secondary">
            {hint}
          </Typography>
        )}
      </Stack>
      {children}
    </Card>
  );
}

function Row({
  label,
  value,
  hint,
  action,
}: {
  label: string;
  value?: string;
  hint?: string;
  action?: React.ReactNode;
}) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={1.5}
      sx={{ justifyContent: "space-between", alignItems: { sm: "center" } }}
    >
      <Stack sx={{ minWidth: 0 }}>
        <Typography sx={{ fontWeight: 600 }}>{label}</Typography>
        {value && (
          <Typography color="text.secondary" noWrap>
            {value}
          </Typography>
        )}
        {hint && (
          <Typography variant="body2" color="text.secondary">
            {hint}
          </Typography>
        )}
      </Stack>
      {action}
    </Stack>
  );
}
