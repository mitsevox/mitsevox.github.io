import {componentScope} from './scope.js';
import {createValueMotion} from './motion.js';

/**
 * @typedef {Object} CountSummaryProps
 * @property {'function'|'file'} kind
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 */
/** Measured inventory counts, sharing markup/animation without deciding report validity. Files add a
 * Closed row, shown only when the report carries the producer's opt-in closed count. @param {CountSummaryProps} props */
export function createCountSummary({kind,scope:parent}) {
  const scope=componentScope(parent),motion=createValueMotion(scope),label=kind==='function'?'Functions':'Files',plural=label.toLowerCase();
  const node=document.createElement('section');node.className='function-stats';node.dataset.stats=kind;node.setAttribute('aria-labelledby',plural+'-title');
  const heading=document.createElement('div');heading.className='stats-heading';
  const title=document.createElement('h2');title.id=plural+'-title';title.textContent=label;
  const total=document.createElement('span');total.className='stats-total';const number=document.createElement('span');number.textContent='—';total.append(number,document.createTextNode(' total'));heading.append(title,total);node.append(heading);
  const fields={};
  for(const field of kind==='file'?['exact','named','closed']:['exact','named']){
    const row=document.createElement('div');row.className='function-stat';row.dataset[kind]=field;if(field==='closed')row.hidden=true;
    const line=document.createElement('div');line.className='stat-heading';const name=document.createElement('h3');name.textContent=field==='exact'?'Exact':field==='named'?'Named':'Closed';
    const count=document.createElement('div');count.className='function-count';const value=document.createElement('strong');value.id=plural+'-'+field;value.textContent='—';count.append(value);line.append(name,count);
    const track=document.createElement('div');track.className='function-track';track.setAttribute('role','progressbar');track.setAttribute('aria-label',label+' '+field);track.setAttribute('aria-valuemin','0');track.setAttribute('aria-valuemax','100');track.setAttribute('aria-valuetext','Loading');const fill=document.createElement('i');track.append(fill);row.append(line,track);node.append(row);fields[field]={row,value,track,fill};
  }
  /** @param {{total:number,exact:number,named:number,closed?:number,basis?:string}|null} counts Already validated by the caller. */
  function update(counts){
    if(scope.signal.aborted)return;
    const available=counts&&counts.basis!=='unavailable'&&counts.total>0;number.textContent=available?counts.total.toLocaleString():'—';
    for(const [field,{row,value,track,fill}] of Object.entries(fields)){
      if(field==='closed'){row.hidden=!(available&&Number.isSafeInteger(counts.closed));if(row.hidden)continue;}
      motion.cancelNumber(value);if(available)motion.number(value,counts[field]);else value.textContent='—';
      motion.fill(fill,available?counts[field]/counts.total*100:0);
      if(available){track.setAttribute('aria-valuenow',counts[field]/counts.total*100);track.setAttribute('aria-valuetext',`${counts[field].toLocaleString()} of ${counts.total.toLocaleString()}`);}
      else{track.removeAttribute('aria-valuenow');track.setAttribute('aria-valuetext','Unavailable');}
    }
  }
  return {node,update,destroy(){scope.destroy();node.remove();}};
}
