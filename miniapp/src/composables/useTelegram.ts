export function useTelegram() {
  const webapp = window.Telegram?.WebApp;
  const ready = () => {
    webapp?.ready();
    webapp?.expand();
    webapp?.setHeaderColor("#0a0b10");
    webapp?.setBackgroundColor("#0a0b10");
    webapp?.enableClosingConfirmation();
  };
  const haptic = (style: "light" | "medium" | "heavy" = "light") => {
    webapp?.HapticFeedback?.impactOccurred(style);
  };
  const success = () => webapp?.HapticFeedback?.notificationOccurred("success");
  const fail = () => webapp?.HapticFeedback?.notificationOccurred("error");
  const openLink = (url: string) => {
    if (webapp?.openLink) webapp.openLink(url);
    else window.open(url, "_blank");
  };
  return { webapp, ready, haptic, success, fail, openLink };
}
