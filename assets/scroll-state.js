// Scroll position is best-effort metadata, never a prerequisite for navigation.
export function createScrollState({history, location, readY, canSave,
  now = () => performance.now(), setTimer = setTimeout, clearTimer = clearTimeout}) {
  const interval = 500;
  let lastWrite = -Infinity, blockedUntil = -Infinity, timer = null;
  function save(flush = false) {
    if (flush && timer !== null) {clearTimer(timer);timer = null;}
    if (!canSave()) return;
    const time = now();
    if (time < blockedUntil) return;
    const y = readY();
    if (history.state?.scrollY === y) return;
    const remaining = interval - (time - lastWrite);
    if (!flush && remaining > 0) {
      if (timer === null) timer = setTimer(() => {timer = null;save();}, remaining);
      return;
    }
    lastWrite = time;
    try {
      history.replaceState({...history.state, scrollY:y}, '', location.href);
    } catch (error) {
      if (error.name !== 'SecurityError') throw error;
      // Safari may already have throttled this document. Stop retrying while
      // its rolling quota recovers, and let the actual navigation continue.
      blockedUntil = time + 10000;
    }
  }
  return {save};
}

export function pushRoute(state, url, history = window.history,
  fallback = destination => window.location.assign(destination)) {
  try {
    history.pushState(state, '', url);
    return true;
  } catch (error) {
    if (error.name !== 'SecurityError') throw error;
    // If the browser also rejects pushState, use a normal document navigation.
    fallback(String(url));
    return false;
  }
}
