"""Local subprocess scheduler; locks are enforced by the CLI."""
import os, subprocess, sys
from apscheduler.schedulers.background import BackgroundScheduler

def _run(*args):
    subprocess.Popen([sys.executable, "-m", "agentdash.cli", *args])


def _pull_and_export():
    subprocess.run([sys.executable, "-m", "agentdash.cli", "state", "pull", "--sources", "p3,global"], check=False)
    subprocess.Popen([sys.executable, "-m", "agentdash.cli", "export"])


def start():
 role=os.getenv('AGENTDASH_ROLE','local-all'); scheduler=BackgroundScheduler()
 if role=='local-all':
  scheduler.add_job(_run,'interval',hours=6,args=('sync','global'),id='global',replace_existing=True)
  scheduler.add_job(_run,'interval',hours=6,args=('sync','p3','--enrich','--max-minutes','50'),id='p3',replace_existing=True)
  scheduler.add_job(_run,'interval',minutes=10,args=('sync','p2','--chunks','1'),id='p2',replace_existing=True)
 elif role=='local-p2':
  scheduler.add_job(_run,'interval',minutes=10,args=('sync','p2','--chunks','1'),id='p2',replace_existing=True)
  scheduler.add_job(_run,'interval',hours=1,args=('state','push','--sources','p2'),id='push-p2',replace_existing=True)
  scheduler.add_job(_pull_and_export,'interval',hours=6,id='pull-export',replace_existing=True)
 scheduler.start(); return scheduler
