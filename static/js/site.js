document.addEventListener("click", async (event) => {
  const button = event.target.closest(".copy-resource-link");
  if (!button) return;

  const link = button.dataset.copyUrl;
  try {
    await navigator.clipboard.writeText(link);
    button.textContent = "Copied!";
    window.setTimeout(() => { button.textContent = "Copy link"; }, 1800);
  } catch {
    window.prompt("Copy this resource link:", link);
  }
});
