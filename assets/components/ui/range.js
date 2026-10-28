/**
 * @typedef {Object} RangeProps
 * @property {string} id
 * @property {string} label
 * @property {number=} min
 * @property {number=} max
 * @property {number=} value
 */
/** Native range keeps browser keyboard, touch, and accessibility semantics. @param {RangeProps} props */
export function createRange({id,label,min=0,max=0,value=0}){
  const node=document.createElement('input');node.type='range';node.id=id;node.min=min;node.max=max;node.value=value;node.setAttribute('aria-label',label);return node;
}
