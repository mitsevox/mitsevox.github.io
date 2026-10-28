import {componentScope} from './scope.js';
import {createAction} from './action.js';

/**
 * @typedef {Object} CodeBlockProps
 * @property {HTMLPreElement} pre Markdown-generated content; its code/language class is retained.
 * @property {ReturnType<typeof import('../../lifecycle.js').pageScope>=} scope
 * @property {(text:string)=>Promise<void>=} writeText Clipboard adapter for testing or host integration.
 */
/** Wrap existing code without reserving a row for the hover/focus copy overlay. @param {CodeBlockProps} props */
export function mountCodeBlock({pre,scope:parent,writeText=text=>navigator.clipboard.writeText(text)}){
  const scope=componentScope(parent),code=pre.querySelector('code');code.textContent=code.textContent.replace(/^\n+|\n+$/g,'');
  const node=document.createElement('div');node.className='wiki-code';
  const actions=document.createElement('div');actions.className='wiki-code-actions';
  const button=createAction({label:'Copy',ariaLabel:'Copy code example',className:'wiki-copy'});
  pre.before(node);node.append(pre,actions);actions.append(button);
  scope.listen(button,'click',async()=>{
    try{await writeText(code.textContent);if(scope.signal.aborted)return;button.textContent='Copied';button.setAttribute('aria-label','Code copied');}
    catch{if(!scope.signal.aborted){button.textContent='Select to copy';button.setAttribute('aria-label','Clipboard unavailable; select the code to copy');}}
  });
  return {node,button,destroy:scope.destroy};
}
