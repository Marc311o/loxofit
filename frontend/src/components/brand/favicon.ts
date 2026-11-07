import { LOGO_VARIANT } from "./logoMarks";

export function applyFavicon(): void {
  let link = document.querySelector<HTMLLinkElement>("link[rel='icon']");
  if (!link) {
    link = document.createElement("link");
    link.rel = "icon";
    link.type = "image/svg+xml";
    document.head.appendChild(link);
  }
  link.href = `/favicons/${LOGO_VARIANT.toLowerCase()}.svg`;
}