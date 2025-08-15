# -*- coding: utf-8 -*-
def js_eval(page, expr, arg=None, label=""):
    """Minimal helper to eval JS safely and not crash the runner."""
    try:
        return page.evaluate(expr, arg)
    except Exception as e:
        print(f"[js_eval:{label}] {e}")
        return None


def install_observer(page, label, primary_sel):
    expr = """
(arg) => {
  const key='__relay_last_'+arg.label;
  if(window[key]) return;

  const avoidIds=new Set(['__relay_seed_btn_gemini','__relay_seed_btn_chapi']);
  const isBad=(el)=>{ while(el){ if(avoidIds.has(el.id)) return true; el=el.parentElement; } return false; };

  const pick=()=>{
    const sels=[arg.primary,"[aria-live=polite] article","main article","[data-message]","article [data-md]","[role='listitem'] article","[role='feed'] > *"].filter(Boolean);
    for(const s of sels){
      try{
        const els=document.querySelectorAll(s);
        if(!els||els.length===0) continue;
        const el=els[els.length-1];
        if(!el||isBad(el)) continue;
        const t=(el.innerText||'').trim();
        if(t) return t;
      }catch(e){}
    }
    // 竊・繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ・壹・繝ｼ繧ｸ蜈ｨ譁・°繧・#relay 縺ｮ譛蠕後・陦後ｒ諡ｾ縺・
    try{
      const lines=(document.body.innerText||'').split(/\\n+/).map(s=>s.trim()).filter(Boolean);
      for(let i=lines.length-1;i>=0;i--){
        const s=lines[i];
        if(/^#relay\\b/.test(s)) return s;
      }
    }catch(e){}
    return null;
  };

  const write=()=>{ try{ window[key]=pick(); }catch(e){} };

  write();
  const target=document.querySelector('main,[aria-live=polite]')||document.body;
  const mo=new MutationObserver(()=>write());
  mo.observe(target,{subtree:true,childList:true,characterData:true});
  window.addEventListener('load', write);
}
"""
    arg = {"label": label, "primary": primary_sel}
    js_eval(page, expr, arg, f"obs:{label}")
    page.on(
        "domcontentloaded", lambda: js_eval(page, expr, arg, f"obs(domready):{label}")
    )
