export const MIN_PASSWORD_LENGTH = 8;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type RegisterForm = {
  email: string;
  displayName: string;
  password: string;
  confirm: string;
};

export type FormErrors<T> = Partial<Record<keyof T, string>>;

export function isEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim());
}

/** Rules shown as a live checklist under the password fields. */
export function passwordRules(password: string, confirm: string) {
  return [
    {
      label: `At least ${MIN_PASSWORD_LENGTH} characters`,
      ok: password.length >= MIN_PASSWORD_LENGTH,
    },
    {
      label: "Both passwords match",
      ok: password.length > 0 && password === confirm,
    },
  ];
}

export function validateRegister(form: RegisterForm): FormErrors<RegisterForm> {
  const errors: FormErrors<RegisterForm> = {};
  if (!form.email.trim()) errors.email = "Enter your email.";
  else if (!isEmail(form.email))
    errors.email = "This does not look like an email address.";
  if (form.password.length < MIN_PASSWORD_LENGTH)
    errors.password = "Password is too short.";
  if (form.confirm !== form.password)
    errors.confirm = "Passwords do not match.";
  return errors;
}
