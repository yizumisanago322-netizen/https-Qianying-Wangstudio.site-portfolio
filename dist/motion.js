(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const panels = [...document.querySelectorAll('.home-main > section:not(.split-hero), .work, .outcome')];
  const observer = new IntersectionObserver(entries => {
    entries.forEach(({target, isIntersecting}) => {
      if (isIntersecting) target.classList.remove('awaiting-entry');
    });
  }, {threshold: 0, rootMargin: '0px 0px -35px 0px'});
  panels.forEach(panel => {
    panel.classList.add('slide-panel');
    if (!reduced.matches && panel.getBoundingClientRect().top > innerHeight) panel.classList.add('awaiting-entry');
    observer.observe(panel);
  });
})();
