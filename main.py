
import os,re,uuid,hmac,threading
from pathlib import Path
from fastapi import FastAPI,UploadFile,File,Form,Header,Depends,HTTPException
from fastapi.responses import FileResponse
from .config import UPLOAD_DIR,OUTPUT_DIR,MAX_UPLOAD_MB
from .db import init_db,add_job,get_job,all_jobs
from .builder import loop
app=FastAPI(title="My Capacitor APK Server",version="1.0.0")
stop=threading.Event(); worker=None
@app.on_event("startup")
def startup():
    global worker
    init_db(); worker=threading.Thread(target=loop,args=(stop,),daemon=True); worker.start()
@app.on_event("shutdown")
def shutdown(): stop.set()
def auth(x_api_key:str=Header(default="")):
    key=os.getenv("API_KEY","")
    if not key: raise HTTPException(503,"API_KEY is not configured")
    if not hmac.compare_digest(key,x_api_key): raise HTTPException(401,"Invalid API key")
def appname(s):
    s=re.sub(r"[^A-Za-z0-9 _.-]","",s).strip()
    return re.sub(r"\\s+"," ",s)[:40] or "My Web App"
def package(s):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z][A-Za-z0-9_]*){1,5}",s):
        raise HTTPException(422,"Use package format com.example.myapp")
    return s
@app.get("/")
def root(): return {"service":"My Capacitor APK Server","docs":"/docs"}
@app.get("/health")
def health(): return {"ok":True,"worker":bool(worker and worker.is_alive())}
@app.post("/api/v1/builds",dependencies=[Depends(auth)])
async def create(file:UploadFile=File(...),app_name:str=Form("My Web App"),package_id:str=Form("com.example.webapp")):
    fname=(file.filename or "").lower()
    if not fname.endswith((".zip",".html",".htm")): raise HTTPException(415,"Upload ZIP or HTML")
    jid=uuid.uuid4().hex; ext=".html" if fname.endswith((".html",".htm")) else ".zip"
    dest=UPLOAD_DIR/(jid+ext); size=0; limit=MAX_UPLOAD_MB*1024*1024
    try:
        with dest.open("wb") as out:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>limit: raise HTTPException(413,f"Maximum upload is {MAX_UPLOAD_MB} MB")
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True); raise
    finally: await file.close()
    add_job(jid,appname(app_name),package(package_id),str(dest))
    return {"job_id":jid,"status":"queued","status_url":f"/api/v1/builds/{jid}"}
@app.get("/api/v1/builds",dependencies=[Depends(auth)])
def jobs(): return {"items":all_jobs()}
@app.get("/api/v1/builds/{jid}",dependencies=[Depends(auth)])
def status(jid:str):
    j=get_job(jid)
    if not j: raise HTTPException(404,"Job not found")
    result={k:j[k] for k in ("id","status","app_name","package_id","created_at","updated_at","error")}
    if j["status"]=="completed": result["download_url"]=f"/api/v1/builds/{jid}/download"
    return result
@app.get("/api/v1/builds/{jid}/download",dependencies=[Depends(auth)])
def download(jid:str):
    j=get_job(jid)
    if not j: raise HTTPException(404,"Job not found")
    if j["status"]!="completed": raise HTTPException(409,"APK is not ready")
    p=Path(j["apk_path"])
    if not p.is_file(): raise HTTPException(410,"APK disappeared after service restart; Render free storage is temporary")
    return FileResponse(p,media_type="application/vnd.android.package-archive",filename=j["app_name"].replace(" ","_")+".apk")
