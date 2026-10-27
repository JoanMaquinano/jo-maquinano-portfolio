(() => {
  const toggle = document.querySelector(".theme-toggle");
  if (!toggle) return;

  const setTheme = (theme) => {
    const isDark = theme === "dark";
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
    toggle.setAttribute("aria-pressed", String(isDark));
    toggle.setAttribute("aria-label", isDark ? "Switch to day mode" : "Switch to night mode");
    toggle.innerHTML = `<span class="theme-toggle-icon" aria-hidden="true">${isDark ? "☀" : "☾"}</span><span>${isDark ? "Day mode" : "Night mode"}</span>`;
  };

  const getPreferredTheme = () => {
    try {
      const savedTheme = localStorage.getItem("portfolio-theme");
      if (savedTheme === "dark" || savedTheme === "light") return savedTheme;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    } catch {
      return "light";
    }
  };

  setTheme(getPreferredTheme());

  toggle.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    try {
      localStorage.setItem("portfolio-theme", nextTheme);
    } catch {
      // The current page still switches themes when storage is unavailable.
    }
  });

  window.addEventListener("storage", (event) => {
    if (event.key === "portfolio-theme" && (event.newValue === "dark" || event.newValue === "light")) {
      setTheme(event.newValue);
    }
  });
})();
