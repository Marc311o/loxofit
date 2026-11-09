import { useState } from "react";
import DirectionsRunRounded from "@mui/icons-material/DirectionsRunRounded";
import { Box } from "@mui/material";

type ExerciseThumbnailProps = {
  imageUrl: string | null;
  size?: number;
};

/** Exercise image, or the exercise icon when there is none (or it fails to load). */
export function ExerciseThumbnail({ imageUrl, size = 48 }: ExerciseThumbnailProps) {
  const [failed, setFailed] = useState(false);
  const showImage = imageUrl !== null && !failed;

  return (
    <Box
      sx={{
        width: size,
        height: size,
        flexShrink: 0,
        borderRadius: 3,
        overflow: "hidden",
        display: "grid",
        placeItems: "center",
        bgcolor: "primary.light",
        color: "primary.dark",
      }}
    >
      {showImage ? (
        <Box
          component="img"
          src={imageUrl}
          alt=""
          loading="lazy"
          onError={() => setFailed(true)}
          sx={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      ) : (
        <DirectionsRunRounded sx={{ fontSize: size * 0.5 }} />
      )}
    </Box>
  );
}
