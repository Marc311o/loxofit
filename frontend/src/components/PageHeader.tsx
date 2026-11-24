import type { ReactNode } from "react";
import { Stack, Typography } from "@mui/material";

type PageHeaderProps = {
  title: string;
  overline?: string;
  subtitle?: string;
  actions?: ReactNode;
};

export function PageHeader({ title, overline, subtitle, actions }: PageHeaderProps) {
  return (
    <Stack
      direction="row"
      sx={{
        alignItems: "flex-end",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 2,
        mb: 3,
      }}
    >
      <Stack spacing={0.5}>
        {overline && (
          <Typography variant="overline" color="text.secondary">
            {overline}
          </Typography>
        )}
        <Typography variant="h1">{title}</Typography>
        {subtitle && <Typography color="text.secondary">{subtitle}</Typography>}
      </Stack>
      {actions && (
        <Stack direction="row" spacing={1.25}>
          {actions}
        </Stack>
      )}
    </Stack>
  );
}
