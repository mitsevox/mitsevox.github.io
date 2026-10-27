import {icon} from './icons.js';

/**
 * @typedef {Object} SearchFieldProps
 * @property {string} label Accessible name.
 * @property {string} placeholder
 * @property {'map'|'hub'|'wiki'=} variant
 * @property {string=} id
 */
/** Native search behavior, with one shared label/icon/input structure. @param {SearchFieldProps} props */
export function createSearchField({label,placeholder,variant='map',id}) {
  const node=document.createElement('label');
  node.className=variant==='wiki'?'wiki-search':'map-search'+(variant==='hub'?' hub-search':'');
  node.append(icon('search',{className:variant==='wiki'?'':'icon',rounded:variant==='map'}));
  const input=document.createElement('input');input.type='search';
  if(id)input.id=id;
  input.placeholder=placeholder;input.setAttribute('aria-label',label);input.autocomplete='off';
  if(variant!=='wiki')input.spellcheck=false;
  node.append(input);
  return {node,input,get value(){return input.value;},setValue(value){input.value=value;}};
}
