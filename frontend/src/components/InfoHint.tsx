import InfoOutlined from "@mui/icons-material/InfoOutlined";
import { IconButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

/**
 * Small (i) button with an explanation: shown on hover and keyboard focus,
 * and on tap on touch screens (no hover there).
 */
export function InfoHint({ text }: { text: string }) {
  const { t } = useTranslation();

  return (
    <Tooltip
      title={text}
      arrow
      describeChild
      enterTouchDelay={0}
      leaveTouchDelay={6000}
      slotProps={{ tooltip: { sx: { fontSize: 13, maxWidth: 280 } } }}
    >
      <IconButton size="small" aria-label={t("moreInfo")} sx={{ p: 0.25, color: "text.secondary" }}>
        <InfoOutlined sx={{ fontSize: 18 }} />
      </IconButton>
    </Tooltip>
  );
}
