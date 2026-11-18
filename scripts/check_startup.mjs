#!/usr/bin/env node
// Recovery must work with neither business script nor translation code loaded.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { harness, response } from "./check_frontend.mjs";
const source = readFileSync(new URL("../mailcairn/static/startup.js", import.meta.url), "utf8");
const html = readFileSync(new URL("../mailcairn/static/index.html", import.meta.url), "utf8");
let passed = 0;
async function check(name, test) { await test(); passed++; console.log("PASS " + name); }
function boot({language="en-US",saved=null,blocked=false,parsing=false}={}) {
  const listeners=new Map(),timers=new Map(),nodes=new Map();let sequence=0,reloads=0;
  const element=id=>({id,hidden:false,disabled:false,textContent:"",events:{},focus(){document.activeElement=this;},contains(node){return node===this||node===nodes.get('startup-reload');},addEventListener(type,fn){this.events[type]=fn;}});
  for(const id of ['startup-recovery','startup-title','startup-message','startup-reload','loading-screen','main-content'])nodes.set(id,element(id));
  nodes.get('startup-recovery').hidden=true;
  const buttons=[element('import'),element('connect'),element('originally-disabled')];buttons[2].disabled=true;
  let domReady=!parsing;
  const document={readyState:parsing?'loading':'complete',getElementById:id=>domReady?nodes.get(id):null,querySelectorAll:()=>buttons,activeElement:null,addEventListener(type,fn){listeners.set('document:'+type,fn);}};
  const window={addEventListener(type,fn){listeners.set(type,fn);},removeEventListener(type,fn){if(listeners.get(type)===fn)listeners.delete(type);}};
  const location={hash:'#session=synthetic-unexchanged-link',reload(){reloads++;}};
  const context=vm.createContext({window,document,location,navigator:{language},localStorage:{getItem(){if(blocked)throw Error('Denied');return saved;}},setTimeout(fn){timers.set(++sequence,fn);return sequence;},clearTimeout(id){timers.delete(id);}});
  vm.runInContext(source,context);
  const emit=(type,event={})=>listeners.get(type)?.({type,...event});
  return{window,document,nodes,buttons,location,listeners,timers,emit,reloads:()=>reloads,parse(){domReady=true;document.readyState='interactive';listeners.get('document:DOMContentLoaded')?.();listeners.delete('document:DOMContentLoaded');},expire(){for(const [id,fn] of [...timers]){timers.delete(id);fn();}}};
}
await check('recovery is local, hidden initially, and precedes both business scripts',()=>{
  assert.ok(html.indexOf('src="/startup.js"')<html.indexOf('src="/i18n.js"'));
  assert.ok(html.indexOf('src="/i18n.js"')<html.indexOf('src="/app.js"'));
  assert.match(html,/<section id="startup-recovery"[^>]*role="alert"[^>]*hidden>/);
  assert.match(html,/<noscript>/);assert.match(html,/<script src="\/startup.js"><\/script>/);assert.doesNotMatch(source,/\b(?:fetch|XMLHttpRequest|innerHTML|eval)\b/);
  const b=boot();assert.equal(b.nodes.get('startup-recovery').hidden,true);assert.equal(b.buttons[0].disabled,false);
});
await check('missing app or translation script shows one usable recovery panel without their globals',()=>{
  for(const name of ['app','i18n']){const b=boot();b.emit('error',{target:{tagName:'SCRIPT',src:'http://127.0.0.1:8765/'+name+'.js'}});assert.equal(b.nodes.get('startup-recovery').hidden,false);assert.equal(b.nodes.get('loading-screen').hidden,true);assert.match(b.nodes.get('startup-title').textContent,/couldn’t load/);assert.ok(b.buttons.every(x=>x.disabled));b.emit('error',{target:{tagName:'SCRIPT',src:'http://127.0.0.1:8765/'+name+'.js'}});assert.equal(b.timers.size,0);}
});
await check('a script failing before body parsing completes is shown after DOM arrival',()=>{
  const b=boot({parsing:true});b.emit('error',{target:{tagName:'SCRIPT',src:'/app.js'}});b.parse();assert.equal(b.nodes.get('startup-recovery').hidden,false);assert.match(b.nodes.get('startup-title').textContent,/couldn’t load/);b.expire();assert.match(b.nodes.get('startup-title').textContent,/couldn’t load/);b.nodes.get('startup-reload').events.click();assert.equal(b.reloads(),1);
});
await check('business parse and top-level errors recover without revealing exception text',()=>{
  for(const file of ['app.js','i18n.js']){const b=boot();b.emit('error',{target:b.window,filename:'http://127.0.0.1:8765/'+file,message:'PRIVATE-DIAGNOSTIC'});assert.equal(b.nodes.get('startup-recovery').hidden,false);assert.ok([...b.nodes.values()].every(n=>!n.textContent.includes('PRIVATE-DIAGNOSTIC')));}
});
await check('font failures and unrelated script exceptions do not replace startup',()=>{
  const b=boot();b.emit('error',{target:{tagName:'LINK',src:'/fonts.css'}});b.emit('error',{target:b.window,filename:'chrome-extension://example/plugin.js'});assert.equal(b.nodes.get('startup-recovery').hidden,true);
});
await check('slow startup stays honest and late success restores only owned state',()=>{
  const b=boot();b.expire();assert.match(b.nodes.get('startup-title').textContent,/still opening/);b.document.activeElement=b.nodes.get('startup-reload');b.window.MailCairnStartup.ready();assert.equal(b.nodes.get('startup-recovery').hidden,true);assert.equal(b.buttons[0].disabled,false);assert.equal(b.buttons[2].disabled,true);assert.equal(b.document.activeElement,b.nodes.get('main-content'));assert.equal(b.listeners.size,0);b.window.MailCairnStartup.fail();assert.equal(b.nodes.get('startup-recovery').hidden,true);
});
await check('successful startup cancels timeout, does not steal focus and ignores later errors',()=>{
  const b=boot();b.document.activeElement=b.buttons[0];b.window.MailCairnStartup.ready();b.expire();b.emit('error',{target:b.window,filename:'/app.js'});assert.equal(b.nodes.get('startup-recovery').hidden,true);assert.equal(b.document.activeElement,b.buttons[0]);assert.equal(b.timers.size,0);
});
await check('saved language wins and denied storage still allows Chinese recovery',()=>{
  for(const options of [{language:'zh-CN',saved:'en'},{language:'en',saved:'zh-CN'},{language:'zh-TW',blocked:true},{language:'en',saved:'invalid'}]){const b=boot(options);b.window.MailCairnStartup.fail();const zh=options.saved==='zh-CN'||(options.saved!=='en'&&options.language.startsWith('zh'));assert.equal(b.nodes.get('startup-recovery').lang,zh?'zh-CN':'en');assert.equal(b.nodes.get('startup-reload').textContent,zh?'重新加载':'Reload page');}
});
await check('native retry reloads exactly once without rewriting the unexchanged session link',()=>{
  const b=boot();b.window.MailCairnStartup.fail();const before=b.location.hash;b.nodes.get('startup-reload').events.click();assert.equal(b.reloads(),1);assert.equal(b.location.hash,before);
});
await check('each early interface-binding failure uses independent recovery before network access',async()=>{
  for(const binding of ['bindLanguage','bindEvents','bindReadingRoom']){const h=harness();let failed=0,requests=0;h.context.window.MailCairnStartup={fail(){failed++;},ready(){throw Error('Must not settle as ready');}};h.context.fetch=()=>{requests++;throw Error('Unexpected request');};h.run(binding+' = () => { throw Error("Synthetic early failure"); }');await h.run('initialize()');assert.equal(failed,1);assert.equal(requests,0);}
});
await check('handled session rejection settles independent fallback and retains unexchanged fragment',async()=>{
  const h=harness();let ready=0;h.context.window.MailCairnStartup={ready(){ready++;},fail(){throw Error('Should render ordinary error');}};h.context.window.location.hash='#session=synthetic-link';h.context.fetch=async()=>response({error:'Session expired'},401);await h.run('initialize()');assert.equal(ready,1);assert.equal(h.nodes.get('#loading-screen').hidden,true);assert.equal(h.context.window.location.hash,'#session=synthetic-link');assert.match(h.nodes.get('#main-content').textContent,/Session expired/);
});
console.log(`${passed} startup checks passed`);
