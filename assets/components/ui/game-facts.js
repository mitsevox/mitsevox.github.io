/**
 * @typedef {Object} GameFactsProps
 * @property {[string,string][]} facts Authored labels and plain-text values.
 */
const paths={
  Developer:'<path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-14-2 18"/>',
  Publisher:'<path d="M5 21V5l7-3 7 3v16M3 21h18M9 7h.01M15 7h.01M9 11h.01M15 11h.01M10 21v-5h4v5"/>',
  Released:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-13 4h2m4 0h2"/>',
  Console:'<path d="M7 7h10c3 0 5 10 3 11s-4-3-5-3H9c-1 0-3 4-5 3S4 7 7 7Z"/><path d="M7 10v4m-2-2h4m7-1h.01m2 2h.01"/>',
  Genre:'<path d="M20 13 13 20a2 2 0 0 1-3 0l-8-8V3h9l9 8a2 2 0 0 1 0 2Z"/><circle cx="7" cy="7" r="1"/>',
  Region:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6.5h14M5 17.5h14"/>'
};
/** A quiet, evenly distributed fact strip. @param {GameFactsProps} props */
export function createGameFacts({facts}){
  const node=document.createElement('dl');node.className='dossier-facts';
  for(const [label,value] of facts){
    const pair=document.createElement('div'),term=document.createElement('dt'),definition=document.createElement('dd');
    const glyph=document.createElement('span');glyph.className='dossier-fact-icon';glyph.setAttribute('aria-hidden','true');
    if(paths[label])glyph.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'+paths[label]+'</svg>';
    term.append(glyph,document.createTextNode(label));definition.textContent=value;pair.append(term,definition);node.append(pair);
  }
  return node;
}
