import {
  LOGO_MARKS,
  LOGO_VARIANT,
  MARK_BG,
  type LogoVariant,
} from "./logoMarks";

interface LogoMarkProps {
  size?: number;
  variant?: LogoVariant;
  title?: string;
}

export function LogoMark({
  size = 32,
  variant = LOGO_VARIANT,
  title = "Loxofit",
}: LogoMarkProps) {
  const mark = LOGO_MARKS[variant];

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label={title}
      style={{ display: "block", flexShrink: 0 }}
    >
      <rect width="48" height="48" rx="13" fill={MARK_BG} />
      {mark.glyph}
    </svg>
  );
}
