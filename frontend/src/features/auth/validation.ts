export const MIN_PASSWORD_LENGTH = 8;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type RegisterForm = {
  email: string;
  displayName: string;
  password: string;
  confirm: string;
};

/** Keys of `auth.validation` - components translate them. */
export type ValidationError =
  "emailRequired" | "emailInvalid" | "passwordRequired" | "passwordTooShort" | "passwordsMismatch";

export type FormErrors<T> = Partial<Record<keyof T, ValidationError>>;

export function isEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim());
}

/** Rules shown as a live checklist under the password fields. */
export function passwordRules(password: string, confirm: string) {
  return [
    { id: "minLength", ok: password.length >= MIN_PASSWORD_LENGTH },
    { id: "match", ok: password.length > 0 && password === confirm },
  ] as const;
}

export function validateRegister(form: RegisterForm): FormErrors<RegisterForm> {
  const errors: FormErrors<RegisterForm> = {};
  if (!form.email.trim()) errors.email = "emailRequired";
  else if (!isEmail(form.email)) errors.email = "emailInvalid";
  if (form.password.length < MIN_PASSWORD_LENGTH) errors.password = "passwordTooShort";
  if (form.confirm !== form.password) errors.confirm = "passwordsMismatch";
  return errors;
}
