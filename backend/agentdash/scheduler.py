"""Local subprocess scheduler; locks are enforced by the CLI."""
import os, subprocess, sys
from apscheduler.schedulers.background import BackgroundScheduler

def _run(*args): subprocess.Popen([sys.executable,'-m','agentdash.cli',*args])
def start():
 role=os.getenv('AGENTDASH_ROLE','local-all'); scheduler=BackgroundScheduler()
 if role=='local-all':
  scheduler.add_job(_run,'interval',hours=6,args=('sync','global'),id='global',replace_existing=True)
  scheduler.add_job(_run,'interval',hours=6,args=('sync','p3','--enrich','--max-minutes','50'),id='p3',replace_existing=True)
  scheduler.add_job(_run,'interval',minutes=10,args=('sync','p2','--chunks','1'),id='p2',replace_existing=True)
 elif role=='local-p2':
  scheduler.add_job(_run,'interval',minutes=10,args=('sync','p2','--chunks','1'),id='p2',replace_existing=True)
  scheduler.add_job(_run,'interval',hours=6,args=('state','pull','--sources','p3,global'),id='pull',replace_existing=True)
  scheduler.add_job(_run,'interval',hours=6,args=('export',),id='export',replace_existing=True)
 scheduler.start(); return scheduler
