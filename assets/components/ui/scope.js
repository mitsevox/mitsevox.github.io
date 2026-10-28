import {pageScope} from '../../lifecycle.js';

/** Independent component lifetime, also disposed when its owning page exits. */
export function componentScope(parent) {
  const scope=pageScope();
  function destroy(){parent?.signal.removeEventListener('abort',destroy);scope.destroy();}
  if(parent?.signal.aborted)destroy();else parent?.signal.addEventListener('abort',destroy,{once:true});
  return {...scope,destroy};
}
