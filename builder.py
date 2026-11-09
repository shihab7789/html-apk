
import shutil, zipfile, subprocess, json
from pathlib import Path, PurePosixPath
from .config import WORK_DIR, OUTPUT_DIR, MAX_EXTRACTED_MB, MAX_FILES, BUILD_TIMEOUT
from .db import claim, update

def command(args,cwd):
    p=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=BUILD_TIMEOUT)
    if p.returncode: raise RuntimeError(p.stdout[-10000:] or "Build command failed")
    return p.stdout[-10000:]

def unzip_checked(src,dst):
    total=0
    with zipfile.ZipFile(src) as z:
        items=z.infolist()
        if len(items)>MAX_FILES: raise ValueError("Too many files in ZIP")
        for i in items:
            n=i.filename.replace("\\\\","/")
            p=PurePosixPath(n)
            if p.is_absolute() or ".." in p.parts: raise ValueError("Unsafe ZIP path rejected")
            if ((i.external_attr>>16)&0o170000)==0o120000: raise ValueError("ZIP symlinks are not allowed")
            total+=i.file_size
            if total>MAX_EXTRACTED_MB*1024*1024: raise ValueError("Unpacked ZIP exceeds size limit")
        z.extractall(dst)

def build(job):
    jid=job["id"]; src=Path(job["source_path"]); work=WORK_DIR/jid
    try:
        work.mkdir(parents=True,exist_ok=True)
        if src.suffix==".html":
            site=work/"site"; site.mkdir(); shutil.copy2(src,site/"index.html")
        else:
            extracted=work/"src"; extracted.mkdir(); unzip_checked(src,extracted)
            indexes=list(extracted.rglob("index.html"))
            if not indexes: raise ValueError("ZIP must contain index.html")
            site=min((x.parent for x in indexes),key=lambda p:len(p.parts))
        project=work/"project"; project.mkdir()
        shutil.copytree(site,project/"www")
        config="import type { CapacitorConfig } from '@capacitor/cli';\nconst config: CapacitorConfig = { appId: "+json.dumps(job["package_id"])+", appName: "+json.dumps(job["app_name"])+", webDir: 'www' };\nexport default config;\n"
        (project/"capacitor.config.ts").write_text(config)
        package={"name":"web-to-apk","version":"1.0.0","private":True,
          "dependencies":{"@capacitor/core":"^6.2.0","@capacitor/android":"^6.2.0"},
          "devDependencies":{"@capacitor/cli":"^6.2.0","typescript":"^5.5.0"}}
        (project/"package.json").write_text(json.dumps(package))
        command(["npm","install","--no-audit","--no-fund"],project)
        command(["npx","cap","add","android"],project)
        android=project/"android"; gradle=android/"gradlew"; gradle.chmod(0o755)
        command(["./gradlew","--no-daemon","assembleDebug"],android)
        apk=android/"app/build/outputs/apk/debug/app-debug.apk"
        if not apk.exists(): raise RuntimeError("APK output missing")
        out=OUTPUT_DIR/(jid+".apk"); shutil.copy2(apk,out)
        update(jid,status="completed",apk_path=str(out),error=None)
    except subprocess.TimeoutExpired:
        update(jid,status="failed",error="Build timed out")
    except Exception as e:
        update(jid,status="failed",error=str(e)[:10000])
    finally:
        shutil.rmtree(work,ignore_errors=True); src.unlink(missing_ok=True)

def loop(stop):
    import time
    while not stop.is_set():
        job=claim()
        if job: build(job)
        else: stop.wait(2)
