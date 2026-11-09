import type { ReactNode } from "react";
import { Stack, Typography } from "@mui/material";

type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
};

/** Placeholder for empty lists, missing resources and failed queries. */
export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <Stack
      spacing={1.5}
      sx={{
        alignItems: "center",
        textAlign: "center",
        py: 6,
        px: 3,
        border: 1,
        borderColor: "divider",
        borderStyle: "dashed",
        borderRadius: 5,
      }}
    >
      {icon && (
        <Stack
          sx={{
            width: 48,
            height: 48,
            borderRadius: 3.5,
            bgcolor: "primary.light",
            color: "primary.dark",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {icon}
        </Stack>
      )}
      <Typography variant="h3">{title}</Typography>
      {description && (
        <Typography color="text.secondary" sx={{ maxWidth: 360 }}>
          {description}
        </Typography>
      )}
      {action}
    </Stack>
  );
}
