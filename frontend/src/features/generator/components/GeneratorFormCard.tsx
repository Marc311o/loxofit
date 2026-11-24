import { useState, type FormEvent } from "react";
import AddRounded from "@mui/icons-material/AddRounded";
import AutoAwesomeRounded from "@mui/icons-material/AutoAwesomeRounded";
import ChevronRightRounded from "@mui/icons-material/ChevronRightRounded";
import RemoveRounded from "@mui/icons-material/RemoveRounded";
import {
  Alert,
  Box,
  Button,
  ButtonBase,
  Card,
  IconButton,
  Link,
  MenuItem,
  Radio,
  Skeleton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router";

import { useMyEquipment } from "@/features/catalog/equipment/api";
import { useWeekdayName } from "@/features/plan/format";
import { MAX_SESSIONS_PER_WEEK } from "@/features/plan/types";
import { ApiError, errorMessage } from "@/lib/api";
import { FONT_MONO } from "@/styles/theme";
import {
  type FormSession,
  type GeneratorForm,
  setSessionCount,
  setTemplate,
  updateSession,
} from "../request";
import { MAX_WEEKS, MIN_WEEKS, type SplitTemplate } from "../types";
import { SessionRequestDialog } from "./SessionRequestDialog";

const TEMPLATES: SplitTemplate[] = ["full_body", "upper_lower", "push_pull_legs", "custom"];
const WEEK_OPTIONS = Array.from({ length: MAX_WEEKS - MIN_WEEKS + 1 }, (_, i) => MIN_WEEKS + i);
const EQUIPMENT_PATH = "/catalog/equipment";

type GeneratorFormCardProps = {
  form: GeneratorForm;
  /** Localized default name of every session ("Upper A"). */
  names: string[];
  onChange: (form: GeneratorForm) => void;
  onSubmit: () => void;
  submitting: boolean;
  /** Why the last start failed. */
  error: unknown;
};

/** What the user fixes: the split, the sessions and the mesocycle length. */
export function GeneratorFormCard({
  form,
  names,
  onChange,
  onSubmit,
  submitting,
  error,
}: GeneratorFormCardProps) {
  const { t } = useTranslation(["generator", "plans"]);
  const equipment = useMyEquipment();
  const [editing, setEditing] = useState<string | null>(null);
  const noEquipment = equipment.data?.length === 0;

  const editedIndex = form.sessions.findIndex((s) => s.key === editing);
  const edited = form.sessions[editedIndex];
  const custom = form.template === "custom";

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  // The dialog stays outside the form: React events bubble through portals, so
  // submitting the dialog would also submit the generator form.
  return (
    <>
      <Card
        component="form"
        aria-label={t("form.label")}
        onSubmit={handleSubmit}
        noValidate
        sx={{ p: 2.5 }}
      >
        <Stack spacing={3}>
          <Stack component="fieldset" spacing={1} sx={{ border: 0, m: 0, p: 0, minWidth: 0 }}>
            <Typography component="legend" variant="overline" color="text.secondary">
              {t("templates.label")}
            </Typography>
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 1 }}>
              {TEMPLATES.map((template) => (
                <TemplateOption
                  key={template}
                  template={template}
                  selected={form.template === template}
                  onSelect={() => onChange(setTemplate(form, template))}
                />
              ))}
            </Box>
          </Stack>

          <Stack spacing={1}>
            <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
              <Typography id="generator-sessions" variant="overline" color="text.secondary">
                {t("form.sessions")}
              </Typography>
              <Stack
                direction="row"
                role="group"
                aria-labelledby="generator-sessions"
                sx={{
                  alignItems: "center",
                  border: 1,
                  borderColor: "divider",
                  borderRadius: 2,
                  height: 36,
                }}
              >
                <IconButton
                  size="small"
                  aria-label={t("form.fewerSessions")}
                  disabled={form.sessions.length <= 1}
                  onClick={() => onChange(setSessionCount(form, form.sessions.length - 1))}
                >
                  <RemoveRounded fontSize="small" />
                </IconButton>
                <Typography
                  aria-live="polite"
                  sx={{ fontFamily: FONT_MONO, fontSize: 14, minWidth: 20, textAlign: "center" }}
                >
                  {form.sessions.length}
                </Typography>
                <IconButton
                  size="small"
                  aria-label={t("form.moreSessions")}
                  disabled={form.sessions.length >= MAX_SESSIONS_PER_WEEK}
                  onClick={() => onChange(setSessionCount(form, form.sessions.length + 1))}
                >
                  <AddRounded fontSize="small" />
                </IconButton>
              </Stack>
            </Stack>
            <Stack
              component="ul"
              sx={{ m: 0, p: 0, listStyle: "none", borderTop: 1, borderColor: "divider" }}
            >
              {form.sessions.map((session, i) => (
                <SessionRow
                  key={session.key}
                  session={session}
                  name={session.name.trim() || names[i]}
                  onEdit={() => setEditing(session.key)}
                />
              ))}
            </Stack>
          </Stack>

          <TextField
            select
            label={t("plans:settings.weeks")}
            value={form.numWeeks}
            onChange={(e) => onChange({ ...form, numWeeks: Number(e.target.value) })}
            helperText={t("plans:settings.weeksHint")}
            fullWidth
          >
            {WEEK_OPTIONS.map((n) => (
              <MenuItem key={n} value={n}>
                {t("plans:settings.weeksOption", { count: n })}
              </MenuItem>
            ))}
          </TextField>

          {equipment.data === undefined ? (
            <Skeleton width="60%" />
          ) : noEquipment ? (
            <Alert
              severity="warning"
              action={
                <Button component={RouterLink} to={EQUIPMENT_PATH} color="inherit" size="small">
                  {t("form.setEquipment")}
                </Button>
              }
            >
              {t("form.noEquipment")}
            </Alert>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t("form.equipment", { count: equipment.data.length })} ·{" "}
              <Link component={RouterLink} to={EQUIPMENT_PATH}>
                {t("form.equipmentChange")}
              </Link>
            </Typography>
          )}

          {error !== null && error !== undefined && (
            <Alert
              severity="error"
              action={
                error instanceof ApiError && error.code === "NO_EXERCISES_FOR_SESSION" ? (
                  <Button component={RouterLink} to={EQUIPMENT_PATH} color="inherit" size="small">
                    {t("form.checkEquipment")}
                  </Button>
                ) : undefined
              }
            >
              {errorMessage(error)}
            </Alert>
          )}

          <Button
            type="submit"
            variant="contained"
            size="large"
            startIcon={<AutoAwesomeRounded />}
            loading={submitting}
            disabled={noEquipment}
          >
            {t("form.submit")}
          </Button>
        </Stack>
      </Card>
      {edited && (
        <SessionRequestDialog
          session={edited}
          defaultName={names[editedIndex]}
          editFocus={custom}
          takenWeekdays={
            new Set(
              form.sessions
                .filter((s) => s.key !== edited.key && s.weekday !== null)
                .map((s) => s.weekday as number),
            )
          }
          onClose={() => setEditing(null)}
          onSave={(change) => {
            onChange(updateSession(form, edited.key, change));
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

function TemplateOption({
  template,
  selected,
  onSelect,
}: {
  template: SplitTemplate;
  selected: boolean;
  onSelect: () => void;
}) {
  const { t } = useTranslation("generator");
  const id = `template-${template}`;

  return (
    <Box
      component="label"
      htmlFor={id}
      sx={{
        display: "flex",
        gap: 0.5,
        alignItems: "flex-start",
        p: 1,
        pr: 1.25,
        border: 1,
        borderRadius: 1,
        cursor: "pointer",
        borderColor: selected ? "primary.main" : "divider",
        bgcolor: selected ? "primary.light" : "transparent",
        transition: "border-color 120ms, background-color 120ms",
        "&:hover": { borderColor: "primary.main" },
        "&:has(:focus-visible)": { outline: 2, outlineColor: "primary.main", outlineOffset: 2 },
      }}
    >
      <Radio
        id={id}
        size="small"
        checked={selected}
        onChange={onSelect}
        name="template"
        value={template}
        sx={{ p: 0.25 }}
      />
      <Stack sx={{ minWidth: 0, pt: 0.125 }}>
        <Typography sx={{ fontSize: 14, fontWeight: 600, lineHeight: 1.3 }}>
          {t(`templates.${template}.label`)}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.35 }}>
          {t(`templates.${template}.description`)}
        </Typography>
      </Stack>
    </Box>
  );
}

function SessionRow({
  session,
  name,
  onEdit,
}: {
  session: FormSession;
  name: string;
  onEdit: () => void;
}) {
  const { t } = useTranslation(["generator", "plans"]);
  const weekdayName = useWeekdayName();
  const meta = [
    session.weekday ? weekdayName(session.weekday) : t("plans:session.noWeekdayShort"),
    t("plans:session.limitShort", { minutes: session.maxMinutes }),
  ]
    .join(" · ")
    .toUpperCase();

  return (
    <Box component="li" sx={{ borderBottom: 1, borderColor: "divider" }}>
      <ButtonBase
        onClick={onEdit}
        aria-label={t("form.editSession", { session: name })}
        sx={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          gap: 1,
          py: 1.25,
          px: 0.5,
          textAlign: "left",
          borderRadius: 1,
          "&:hover": { bgcolor: "action.hover" },
        }}
      >
        <Stack sx={{ minWidth: 0 }}>
          <Typography noWrap sx={{ fontSize: 14, fontWeight: 600 }}>
            {name}
          </Typography>
          <Typography sx={{ fontFamily: FONT_MONO, fontSize: 11, color: "text.secondary" }}>
            {meta}
          </Typography>
        </Stack>
        <ChevronRightRounded sx={{ color: "text.secondary" }} />
      </ButtonBase>
    </Box>
  );
}
