/* One passive controller, scoped to explicitly opted-in publication figures. */
(() => {
  const visuals = [...document.querySelectorAll('[data-editorial-visual]')];
  if (!visuals.length) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = matchMedia('(max-width: 767px)');
  let frame = 0;
  const smooth = t => t * t * (3 - 2 * t);
  const update = () => {
    frame = 0;
    const disabled = reduced.matches || mobile.matches;
    const measures = visuals.map(element => ({element, rect:element.getBoundingClientRect(), max:parseFloat(getComputedStyle(element).getPropertyValue('--editorial-darkness-max')) || .4}));
    measures.forEach(({element,rect,max}) => {
      // Starts when the visual reaches the viewport top; clears before the following text.
      const progress = Math.max(0, Math.min(1, -rect.top / Math.max(1,rect.height)));
      const envelope = progress < .5 ? smooth(progress * 2) : smooth((1 - progress) * 2);
      element.style.setProperty('--editorial-opacity', disabled ? 0 : Math.min(.45,max) * envelope);
    });
  };
  const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };
  addEventListener('scroll',schedule,{passive:true});
  addEventListener('resize',schedule,{passive:true});
  reduced.addEventListener('change',schedule); mobile.addEventListener('change',schedule);
  addEventListener('load',schedule,{once:true}); update();
})();
