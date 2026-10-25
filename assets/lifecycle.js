// A page owns its listeners, pending requests, and motion; the shell outlives it.
export function pageScope() {
  const controller = new AbortController();
  const frames = new Set(), animations = new Set();
  const signal = controller.signal;
  const listen = (target, type, listener, options = {}) => target.addEventListener(type, listener, {...options, signal});
  const frame = callback => {
    if (signal.aborted) return null;
    const id = window.requestAnimationFrame(time => {
      frames.delete(id);
      if (!signal.aborted) callback(time);
    });
    frames.add(id);
    return id;
  };
  const cancelFrame = id => { window.cancelAnimationFrame(id); frames.delete(id); };
  const animate = (element, keyframes, options) => {
    const animation = element.animate(keyframes, options);
    animations.add(animation);
    animation.finished.then(() => animations.delete(animation), () => animations.delete(animation));
    return animation;
  };
  const destroy = () => {
    controller.abort();
    for (const id of frames) window.cancelAnimationFrame(id);
    for (const animation of animations) animation.cancel();
    frames.clear(); animations.clear();
  };
  return {signal, listen, frame, cancelFrame, animate, destroy};
}
