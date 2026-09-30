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
  const hero = document.querySelector('.split-hero');
  if (!hero) return;
  let pending = false;
  const update = () => {
    pending = false;
    const distance = Math.max(0, scrollY - hero.offsetTop);
    const progress = Math.min(1, distance / Math.max(1, hero.offsetHeight * .85));
    hero.style.transform = reduced.matches ? '' : `translateY(${-progress * 140}px)`;
    hero.style.opacity = reduced.matches ? '' : String(1 - progress);
  };
  addEventListener('scroll', () => {if (!pending) {pending = true; requestAnimationFrame(update);}}, {passive:true});
  addEventListener('resize', update);
  reduced.addEventListener('change', update);
  update();
})();
