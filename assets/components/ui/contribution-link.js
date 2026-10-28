import {createAction} from './action.js';
import {icon} from './icons.js';

/**
 * @typedef {Object} ContributionLinkProps
 * @property {string=} href
 * @property {'header'|'callout'=} variant
 * @property {boolean=} hidden
 */
/** The shared contribution action; project configuration still decides visibility. @param {ContributionLinkProps} props */
export function createContributionLink({href,variant='header',hidden=false}={}){
  const node=createAction({as:'a',href,icon:'contribution',className:variant==='header'?'contribute-link':undefined,ariaLabel:variant==='header'?'Contribute':undefined,hidden});
  const label=document.createElement('span');label.textContent=variant==='header'?'Contribute':'Start contributing';node.append(label);
  if(variant==='callout')node.append(icon('external',{className:'icon external-icon'}));
  return node;
}
