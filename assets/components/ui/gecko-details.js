/**
 * @typedef {Object} GeckoDetailsProps
 * @property {string} code Display-only code lines; full INI copying stays with the existing control.
 * @property {string} description Owner-authored description, rendered as text.
 * @property {string=} author Credit from the INI header.
 * @property {string=} category Optional code category: Graphics, Gameplay or Cheats.
 * @property {string} title Accessible name for the code block.
 */
const glyphs={
  Author:'<circle cx="12" cy="8" r="3"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/>',
  Category:'<path d="M20 13 13 20a2 2 0 0 1-3 0l-8-8V3h9l9 8a2 2 0 0 1 0 2Z"/><circle cx="7" cy="7" r="1"/>',
  Length:'<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>'
};
/** Description-first code detail with centered properties and a bounded code column.
 * @param {GeckoDetailsProps} props */
export function createGeckoDetails({code,description,author,category,title}){
  const node=document.createElement('div');node.className='dossier-code-body gecko-detail';
  const narrative=document.createElement('div');narrative.className='gecko-narrative';
  if(description){const copy=document.createElement('p');copy.className='dossier-code-notes';copy.textContent=description;narrative.append(copy);}
  const facts=document.createElement('dl');facts.className='gecko-properties';
  const lineCount=code?code.split('\n').length:0;
  for(const [label,value] of [['Author',author],['Category',category],['Length',lineCount+' '+(lineCount===1?'line':'lines')]]){
    if(!value)continue;
    const cell=document.createElement('div'),term=document.createElement('dt'),definition=document.createElement('dd');
    const glyph=document.createElement('span');glyph.setAttribute('aria-hidden','true');glyph.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'+glyphs[label]+'</svg>';
    term.append(glyph,document.createTextNode(label));definition.textContent=value;cell.append(term,definition);facts.append(cell);
  }
  facts.style.gridTemplateColumns='repeat('+facts.children.length+',minmax(0,1fr))';
  narrative.append(facts);
  const pre=document.createElement('pre');pre.textContent=code;pre.setAttribute('aria-label',title+' Gecko code');pre.tabIndex=0;
  node.append(narrative,pre);return node;
}
