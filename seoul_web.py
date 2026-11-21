"""Seoul IA FiveM: local-only web panel and multi-provider chat gateway."""
from __future__ import annotations
import json
import os
import secrets
import threading
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from core.auto_framework_detector import detect_frameworks

ROOT = Path(__file__).resolve().parent
PREFS = ROOT / "data" / "seoul_web_settings.json"
DEFAULTS = {"mode":"local","provider":"ollama","model":"qwen2.5-coder:7b","fallbacks":[]}
PROVIDERS = {
 "ollama": {"env":None,"default":"qwen2.5-coder:7b"},
 "openai": {"env":"OPENAI_API_KEY","default":"gpt-4.1-mini"},
 "gemini": {"env":"GEMINI_API_KEY","default":"gemini-2.5-flash"},
 "anthropic": {"env":"ANTHROPIC_API_KEY","default":"claude-sonnet-4-5"},
 "openrouter": {"env":"OPENROUTER_API_KEY","default":"openai/gpt-4.1-mini"},
}
API_KEYS = {}  # only in process memory; never written to disk
TOKEN = secrets.token_urlsafe(32)

def prefs():
 try:
  data=json.loads(PREFS.read_text(encoding="utf-8"))
  return {**DEFAULTS,**{k:v for k,v in data.items() if k in DEFAULTS}}
 except (OSError,ValueError): return DEFAULTS.copy()

def request_json(url,payload=None,headers=None,method=None,timeout=60):
 data=None if payload is None else json.dumps(payload).encode("utf-8")
 req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json",**(headers or {})},method=method)
 try:
  with urllib.request.urlopen(req,timeout=timeout) as resp:
   return json.loads(resp.read(4_000_000).decode("utf-8"))
 except urllib.error.HTTPError as e:
  msg=e.read(500).decode("utf-8","replace")
  raise RuntimeError(f"HTTP {e.code}: {msg}") from None

def chat(provider,model,messages):
 if provider not in PROVIDERS: raise ValueError("Provedor inválido")
 key=API_KEYS.get(provider) or os.environ.get(PROVIDERS[provider]["env"] or "", "")
 if provider!="ollama" and not key: raise RuntimeError(f"Chave não configurada: {provider}")
 if provider=="ollama":
  r=request_json("http://127.0.0.1:11434/api/chat",{"model":model,"messages":messages,"stream":False},timeout=180)
  return r["message"]["content"]
 if provider=="gemini":
  contents=[{"role":"model" if m["role"]=="assistant" else "user","parts":[{"text":m["content"]}]} for m in messages]
  r=request_json("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent",{"contents":contents},headers={"x-goog-api-key":key})
  return "".join(p.get("text","") for p in r["candidates"][0]["content"]["parts"])
 if provider=="anthropic":
  r=request_json("https://api.anthropic.com/v1/messages",{"model":model,"max_tokens":2048,"messages":[m for m in messages if m["role"]!="system"]},headers={"x-api-key":key,"anthropic-version":"2023-06-01"})
  return "".join(c.get("text","") for c in r["content"] if c.get("type")=="text")
 url="https://api.openai.com/v1/chat/completions" if provider=="openai" else "https://openrouter.ai/api/v1/chat/completions"
 r=request_json(url,{"model":model,"messages":messages},headers={"Authorization":"Bearer "+key})
 return r["choices"][0]["message"]["content"]

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def send(self,obj,status=200):
  raw=json.dumps(obj,ensure_ascii=False).encode("utf-8")
  self.send_response(status)
  self.send_header("Content-Type","application/json; charset=utf-8")
  self.send_header("Cache-Control","no-store")
  self.send_header("Content-Length",str(len(raw)))
  self.end_headers();self.wfile.write(raw)
 def allowed(self):
  host=self.headers.get("Host","").split(":")[0].lower()
  origin=self.headers.get("Origin","")
  return host in ("127.0.0.1","localhost") and (not origin or urlsplit(origin).hostname in ("127.0.0.1","localhost"))
 def authorized(self):
  return self.headers.get("X-Seoul-Token")==TOKEN
 def do_GET(self):
  if not self.allowed(): return self.send({"error":"Origem bloqueada"},403)
  if self.path.startswith("/api/"):
   if not self.authorized(): return self.send({"error":"Não autorizado"},403)
   if self.path=="/api/settings":
    return self.send({"settings":prefs(),"providers":{k:{"configured":k=="ollama" or bool(API_KEYS.get(k) or os.environ.get(v["env"] or "")),"default":v["default"]} for k,v in PROVIDERS.items()}})
   return self.send({"error":"Rota desconhecida"},404)
  if self.path not in ("/","/index.html"): return self.send({"error":"Não encontrado"},404)
  html=(ROOT/"web"/"index.html").read_text(encoding="utf-8").replace("__SEOUL_TOKEN__",TOKEN)
  raw=html.encode("utf-8")
  self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8")
  self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(raw)))
  self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  if not self.allowed() or not self.authorized(): return self.send({"error":"Não autorizado"},403)
  try:
   size=int(self.headers.get("Content-Length","0"))
   if size<1 or size>200_000: return self.send({"error":"Tamanho inválido"},400)
   data=json.loads(self.rfile.read(size))
   if self.path=="/api/settings":
    new=prefs()
    for k in ("mode","provider","model","fallbacks"):
     if k in data: new[k]=data[k]
    if new["mode"] not in ("local","online","auto") or new["provider"] not in PROVIDERS or not isinstance(new["model"],str) or len(new["model"])>150: raise ValueError("Configuração inválida")
    if not isinstance(new["fallbacks"],list) or any(not isinstance(x,dict) or x.get("provider") not in PROVIDERS or not isinstance(x.get("model"),str) for x in new["fallbacks"]): raise ValueError("Fallbacks inválidos")
    PREFS.parent.mkdir(exist_ok=True)
    PREFS.write_text(json.dumps(new,indent=2,ensure_ascii=False),encoding="utf-8")
    return self.send({"ok":True})
   if self.path=="/api/key":
    provider=data.get("provider");key=data.get("key")
    if provider not in PROVIDERS or provider=="ollama" or not isinstance(key,str) or len(key)>500: raise ValueError("Chave inválida")
    if key: API_KEYS[provider]=key.strip()
    else: API_KEYS.pop(provider,None)
    return self.send({"ok":True})
   if self.path=="/api/detect":
    path=data.get("path","")
    if not isinstance(path,str) or not path.strip(): raise ValueError("Selecione uma pasta")
    return self.send(detect_frameworks(path))
   if self.path=="/api/chat":
    message=data.get("message","")
    history=data.get("history",[])
    if not isinstance(message,str) or not message.strip() or len(message)>12000: raise ValueError("Mensagem inválida")
    if not isinstance(history,list) or len(history)>16 or any(not isinstance(m,dict) or m.get("role") not in ("user","assistant") or not isinstance(m.get("content"),str) or len(m["content"])>12000 for m in history): raise ValueError("Histórico inválido")
    config=prefs()
    primary={"provider":config["provider"],"model":config["model"]}
    candidates=([primary]+config["fallbacks"]) if config["mode"]=="auto" else [primary]
    if config["mode"]=="local": candidates=[{"provider":"ollama","model":config["model"]}]
    if config["mode"]=="online" and config["provider"]=="ollama": raise ValueError("Escolha um provedor online")
    errors=[]
    for item in candidates:
     try:
      answer=chat(item["provider"],item["model"],history+[{"role":"user","content":message}])
      return self.send({"answer":answer,"provider":item["provider"],"model":item["model"],"attempts":errors})
     except (RuntimeError,ValueError,KeyError,IndexError,urllib.error.URLError,TimeoutError) as e:
      errors.append({"provider":item["provider"],"error":str(e)[:300]})
    return self.send({"error":"Nenhum provedor respondeu","attempts":errors},502)
   return self.send({"error":"Rota desconhecida"},404)
  except (ValueError,TypeError,KeyError) as e: return self.send({"error":str(e)},400)
  except Exception as e: return self.send({"error":str(e)[:300]},500)

def main():
 server=ThreadingHTTPServer(("127.0.0.1",8765),Handler)
 url="http://127.0.0.1:8765/"
 print("Seoul IA FiveM Web:",url)
 threading.Timer(0.8,lambda:webbrowser.open(url)).start()
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 finally: server.server_close()

if __name__=="__main__": main()
