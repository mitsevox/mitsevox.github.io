// Trusted site-owned glyphs. Consumer text never enters SVG markup.
const paths={
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  commit:'<path d="M3 12h5m8 0h5"/><circle cx="12" cy="12" r="4"/>',
  clock:'<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/>',
  code:'<path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-14-2 18"/>',
  data:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/>',
  back:'<path d="m12 5-7 7 7 7M5 12h14"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',
  contribution:'<path d="M8 4v10a4 4 0 0 0 4 4h4M16 4v4a4 4 0 0 1-4 4H8"/><circle cx="8" cy="4" r="2"/><circle cx="16" cy="4" r="2"/><circle cx="18" cy="18" r="2"/>',
  external:'<path d="M7 17 17 7M7 7h10v10"/>'
};
/** @param {keyof typeof paths} name @param {{className?:string,rounded?:boolean}} options */
export function icon(name,{className='icon',rounded=name!=='close'}={}) {
  if(!paths[name])throw Error('Unknown UI icon: '+name);
  const template=document.createElement('template');
  template.innerHTML=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"${rounded?' stroke-linecap="round" stroke-linejoin="round"':''}>${paths[name]}</svg>`;
  const node=template.content.firstElementChild;
  if(className)node.setAttribute('class',className);
  return node;
}
