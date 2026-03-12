/* EQBuffBot — Page Script */

// Highlight the active nav link based on scroll position
(function () {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.main-nav a');

  if (!sections.length || !navLinks.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          navLinks.forEach((link) => {
            if (link.getAttribute('href') === `#${id}`) {
              link.style.color = 'var(--gold-light)';
              link.style.borderBottomColor = 'var(--gold)';
            } else {
              link.style.color = '';
              link.style.borderBottomColor = '';
            }
          });
        }
      });
    },
    { rootMargin: '-30% 0px -60% 0px' }
  );

  sections.forEach((s) => observer.observe(s));
})();

// Fade-in sections as they enter the viewport
(function () {
  const panels = document.querySelectorAll('.panel, .use-case-card, .pipeline-step');

  const style = document.createElement('style');
  style.textContent = `
    .fade-target { opacity: 0; transform: translateY(18px); transition: opacity 0.5s ease, transform 0.5s ease; }
    .fade-target.visible { opacity: 1; transform: translateY(0); }
  `;
  document.head.appendChild(style);

  panels.forEach((el) => el.classList.add('fade-target'));

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  panels.forEach((el) => observer.observe(el));
})();
