import {icon} from './icons.js';

/**
 * @typedef {Object} ActionProps
 * @property {string=} label Visible text, rendered as text rather than HTML.
 * @property {string=} ariaLabel Required when the action has no visible text.
 * @property {string=} href Normal links retain native navigation/modifier behavior.
 * @property {'button'|'a'=} as
 * @property {string=} id
 * @property {string=} className Existing visual variant, without a new default style.
 * @property {Parameters<typeof icon>[0]=} icon
 * @property {boolean=} hidden
 * @property {boolean=} disabled
 */
/** @param {ActionProps} props */
export function createAction(props={}) {
  const node=document.createElement(props.as==='a'||props.href!==undefined?'a':'button');
  if(node.tagName==='BUTTON')node.type='button';
  if(props.href!==undefined)node.href=props.href;
  if(props.id)node.id=props.id;
  if(props.className)node.className=props.className;
  if(props.ariaLabel)node.setAttribute('aria-label',props.ariaLabel);
  if(props.icon)node.append(icon(props.icon));
  if(props.label!==undefined)node.append(document.createTextNode(props.label));
  node.hidden=!!props.hidden;
  if(props.disabled&&node.tagName==='BUTTON')node.disabled=true;
  return node;
}
