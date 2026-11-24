import { Box, Stack } from "@mui/material";

type DotScaleProps = {
  value: number;
  max?: number;
  label: string;
};

export function DotScale({ value, max = 5, label }: DotScaleProps) {
  return (
    <Stack direction="row" spacing={0.5} role="img" aria-label={label}>
      {Array.from({ length: max }, (_, index) => (
        <Box
          key={index}
          sx={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            border: 2,
            borderColor: "primary.main",
            bgcolor: index < value ? "primary.main" : "transparent",
          }}
        />
      ))}
    </Stack>
  );
}
