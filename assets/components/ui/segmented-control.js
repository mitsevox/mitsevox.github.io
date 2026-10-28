import {componentScope} from './scope.js';
import {createAction} from './action.js';

/**
 * @typedef {Object} SegmentedControlProps
 * @property {string} id
 * @property {string} label
 * @property {string} value
 * @property {{value:string,label:string,icon?:Parameters<typeof createAction>[0]['icon']}[]} options
 * @property {(value:string,event:MouseEvent,button:HTMLButtonElement)=>void=} onChange
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 */
/** Native pressed buttons preserve Tab/Enter/Space and the existing sliding indicator. @param {SegmentedControlProps} props */
export function createSegmentedControl(props){
  const scope=componentScope(props.scope),node=document.createElement('div');node.id=props.id;node.className='map-toggle';node.setAttribute('role','group');node.setAttribute('aria-label',props.label);
  const buttons=new Map();
  for(const option of props.options){
    if(buttons.has(option.value))throw Error('Duplicate segment: '+option.value);
    const button=createAction({icon:option.icon});button.dataset.kind=option.value;
    const text=document.createElement('span');text.textContent=option.label;button.append(text);buttons.set(option.value,button);node.append(button);
    scope.listen(button,'click',event=>{setValue(option.value);props.onChange?.(option.value,event,button);});
  }
  function setValue(value){if(!buttons.has(value))throw Error('Unknown segment: '+value);node.dataset.selected=value;for(const [key,button] of buttons)button.setAttribute('aria-pressed',String(key===value));}
  setValue(props.value);
  return {node,setValue,destroy(){scope.destroy();node.remove();}};
}
