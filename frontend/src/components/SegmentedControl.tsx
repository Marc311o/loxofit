import type { ReactNode } from "react";
import { Box, ToggleButton, ToggleButtonGroup } from "@mui/material";
import { Link as RouterLink } from "react-router";

export type SegmentOption<T extends string | number> = {
  value: T;
  label: string;
  icon?: ReactNode;
  to?: string;
  disabled?: boolean;
};

type SegmentedControlProps<T extends string | number> = {
  options: SegmentOption<T>[];
  value: T | null;
  onChange?: (value: T) => void;
  label: string;
  fullWidth?: boolean;
  iconsOnlyOnPhone?: boolean;
};

export function SegmentedControl<T extends string | number>({
  options,
  value,
  onChange,
  label,
  fullWidth = false,
  iconsOnlyOnPhone = false,
}: SegmentedControlProps<T>) {
  return (
    <Box sx={{ maxWidth: "100%", overflowX: "auto", flexShrink: fullWidth ? 1 : 0 }}>
      <ToggleButtonGroup
        exclusive
        size="small"
        value={value}
        onChange={(_, next: T | null) => {
          if (next !== null) onChange?.(next);
        }}
        aria-label={label}
        sx={fullWidth ? { width: "100%", minWidth: "max-content" } : undefined}
      >
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <ToggleButton
              key={option.value}
              value={option.value}
              disabled={option.disabled}
              aria-label={option.label}
              aria-current={option.to && selected ? "page" : undefined}
              {...(option.to ? { component: RouterLink, to: option.to } : {})}
              sx={{
                gap: 1,
                px: { xs: 1.5, sm: 2 },
                fontWeight: 600,
                whiteSpace: "nowrap",
                flex: fullWidth ? "1 0 0" : undefined,
                minWidth: fullWidth ? "max-content" : undefined,
                "&.Mui-selected, &.Mui-selected:hover": {
                  bgcolor: "primary.light",
                  color: "primary.dark",
                },
              }}
            >
              {option.icon}
              <Box
                component="span"
                sx={{
                  display:
                    iconsOnlyOnPhone && option.icon ? { xs: "none", sm: "inline" } : "inline",
                }}
              >
                {option.label}
              </Box>
            </ToggleButton>
          );
        })}
      </ToggleButtonGroup>
    </Box>
  );
}
