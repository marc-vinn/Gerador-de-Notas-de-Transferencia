/**
 * Security Sanitization Utilities
 * Protects against Cross-Site Scripting (XSS) and DOM injections.
 */

export function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function sanitizeDigits(str) {
  if (!str) return "";
  return String(str).replace(/\D/g, "");
}
