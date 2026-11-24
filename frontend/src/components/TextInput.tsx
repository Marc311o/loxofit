import { useState, type ReactNode } from "react";
import VisibilityOffOutlined from "@mui/icons-material/VisibilityOffOutlined";
import VisibilityOutlined from "@mui/icons-material/VisibilityOutlined";
import { IconButton, InputAdornment, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";

type TextInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  name?: string;
  type?: "text" | "email" | "search";
  /** Hidden input with a show/hide toggle. */
  password?: boolean;
  icon?: ReactNode;
  placeholder?: string;
  autoComplete?: string;
  autoFocus?: boolean;
  required?: boolean;
  disabled?: boolean;
  /** Red outline without a message - e.g. both fields after a failed login. */
  error?: boolean;
  /** Red message under the field; implies `error`. */
  errorText?: string;
  helperText?: string;
};

export function TextInput({
  label,
  value,
  onChange,
  name,
  type = "text",
  password = false,
  icon,
  placeholder,
  autoComplete,
  autoFocus,
  required,
  disabled,
  error = false,
  errorText,
  helperText,
}: TextInputProps) {
  const { t } = useTranslation();
  const [visible, setVisible] = useState(false);
  const hasError = error || Boolean(errorText);

  return (
    <TextField
      label={label}
      name={name}
      value={value}
      type={password && !visible ? "password" : type}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      autoComplete={autoComplete}
      autoFocus={autoFocus}
      required={required}
      disabled={disabled}
      error={hasError}
      helperText={errorText || helperText}
      fullWidth
      slotProps={{
        input: {
          startAdornment: icon ? (
            <InputAdornment position="start">{icon}</InputAdornment>
          ) : undefined,
          endAdornment: password ? (
            <InputAdornment position="end">
              <IconButton
                aria-label={visible ? t("password.hide") : t("password.show")}
                onClick={() => setVisible((v) => !v)}
                edge="end"
                disabled={disabled}
              >
                {visible ? <VisibilityOffOutlined /> : <VisibilityOutlined />}
              </IconButton>
            </InputAdornment>
          ) : undefined,
        },
      }}
      sx={{
        "& .MuiInputAdornment-root": {
          color: hasError ? "error.main" : "text.secondary",
        },
      }}
    />
  );
}
