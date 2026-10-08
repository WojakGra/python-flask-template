// Auto-close flash messages after 3 s. htmx.onLoad also fires for the initial page.
htmx.onLoad((root) => {
  root.querySelectorAll(".alert-dismissible").forEach((el) =>
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(el).close(), 3000),
  );
});
