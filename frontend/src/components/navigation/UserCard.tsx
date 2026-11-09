import LogoutRounded from "@mui/icons-material/LogoutRounded";
import { Avatar, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useCurrentUser, useLogout } from "@/features/auth/api";

export function UserCard() {
  const { t } = useTranslation("nav");
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const name = user?.display_name || user?.email.split("@")[0] || "";

  return (
    <Stack
      direction="row"
      spacing={1.25}
      sx={{
        alignItems: "center",
        p: 1.25,
        borderRadius: 1,
        bgcolor: "background.default",
      }}
    >
      <Avatar
        sx={{
          width: 36,
          height: 36,
          bgcolor: "primary.light",
          color: "primary.dark",
          fontWeight: 600,
        }}
      >
        {name.charAt(0).toUpperCase()}
      </Avatar>
      <Typography noWrap sx={{ flex: 1, fontSize: 14, fontWeight: 600 }}>
        {name}
      </Typography>
      <Tooltip title={t("logout")}>
        <IconButton
          aria-label={t("logout")}
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
        >
          <LogoutRounded fontSize="small" />
        </IconButton>
      </Tooltip>
    </Stack>
  );
}
