(() => {
  "use strict";
  const sections = [...document.querySelectorAll("main > section[id]")];
  const links = [...document.querySelectorAll("#section-nav a")];

  const setCurrent = (id) => {
    links.forEach((link) => {
      if (link.hash === "#" + id) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  };

  const updateNavigation = () => {
    if (!sections.length) return;
    // The final section may never reach the top of a short viewport's last page.
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) {
      setCurrent(sections[sections.length - 1].id);
      return;
    }
    const threshold = window.innerWidth <= 900 ? 100 : 120;
    const current = sections.filter((section) => section.getBoundingClientRect().top <= threshold).pop();
    setCurrent(current ? current.id : null);
  };
  let navigationScheduled = false;
  const scheduleNavigation = () => {
    if (navigationScheduled) return;
    navigationScheduled = true;
    window.requestAnimationFrame(() => {
      updateNavigation();
      navigationScheduled = false;
    });
  };
  window.addEventListener("scroll", scheduleNavigation, { passive: true });
  window.addEventListener("resize", scheduleNavigation);
  updateNavigation();
  links.forEach((link) => link.addEventListener("click", () => setCurrent(link.hash.slice(1))));

  if (!("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.remove("pending-reveal");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px 80px 0px", threshold: 0 });
  document.documentElement.classList.add("reveal-enabled");
  sections.forEach((section) => {
    if (section.getBoundingClientRect().top > window.innerHeight) section.classList.add("pending-reveal");
    revealObserver.observe(section);
  });
})();
