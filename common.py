import glob
import logging
import re
import shutil
import signal
import time

from flask import *
from json import dumps

from backend.config import *

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def check_class(obj, allowed_types):
  results = [isinstance(obj, some_type) for some_type in allowed_types]
  if (False in results):
    logging.debug(obj.__class__)
  # logging.debug(results)
  return (True in results)


def check_list_item_types(some_list, allowed_types):
  check_class_results = [check_class(item, allowed_types=allowed_types) for item in some_list]
  # logging.debug(check_class_results)
  return not (False in check_class_results)


def wl_batchprocess(args, cmd, func):
  wloads = args.get('wlnames').split(',')
  print "In wl" + cmd
  print dumps(wloads)
  return (make_response(dumps(func(args))))


def urlize(pathsuffix, text=None, newtab=True):
  tabclause = ""
  if newtab:
    tabclause = 'target="_blank"'
  if not text:
    text = pathsuffix
  return '<a href="/workloads/taillog/15/' + pathsuffix + '" ' + tabclause + '>' + text + '</a>'


def get_all_jsons(path, pattern):
  """
  path    -    where to begin folder scan
  """

  pathprefix = repodir()
  selected_files = []
  print pathprefix
  full_path = None
  for root, dirs, files in os.walk(path, followlinks=True):
    for f in files:
      full_path = join(root, f)
      ext = splitext(f)[1]

      if ext != ".json":
        continue
      wpath = full_path.replace(pathprefix + "/", "")
      # print "wpath:",wpath
      if pattern and not re.search(pattern, full_path):
        continue
      selected_files.append(wpath)

  return selected_files


subprocs = set()


def signal_children(subprocs, signum):
  sent_signal = False
  for proc in subprocs:
    if proc.poll() is None:
      sent_signal = True
      print "wlwizard child: Killing " + str(proc.pid)
      try:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
      except Exception as e:
        print e
        return False
        # proc.send_signal(signum)
  return sent_signal


def handle_signal(signum, frame):
  print "wlwizard child: caught signal " + str(signum) + " .."

  try:
    while signal_children(subprocs, signum) == True:
      print "wlwizard handler: sleeping"
      time.sleep(10)
  except Exception as e:
    print "wlwizard handler: ", e


def fork_work(wloadname, cmdname, func, params=None):
  params = params or {}
  # workload_dirpath = pubroot()+'/'
  wdir = join(repodir(), wloadname)
  createdir(wdir)  # create workload-directory inside parsed folder
  logfile = join(wdir, cmdname + "-log.txt")
  pidfile = join(wdir, cmdname + ".pid")
  print "pidfile:", pidfile
  pid = os.fork()
  if pid == 0:
    # Child
    os.setsid()
    mypid = os.getpid()
    #        try:
    #            Flask(__name__).stop()
    #        except Exception as e:
    #            print "Error closing server socket:", e

    with open(logfile, 'w', 1) as f:
      # Redirect stdout and stderr to logfile
      sys.stdout = sys.stderr = f
      ret = 1
      with open(pidfile, 'w') as f:
        f.write(str(mypid))

      try:
        os.chdir(wdir)
        ret = func(wdir, wloadname, cmdname, params)
      except Exception as e:
        print "wlwizard fork_child: ", e

      print "wlwizard fork_child: removing pid file" + join(wdir, cmdname + ".pid")
      print "wlwizard: Workdir: ", wdir
      os.remove(join(wdir, cmdname + ".pid"))
      print "wlwizard: in child, exiting"
      os._exit(ret)

  # Parent
  return 'Started. ' + urlize(join(wloadname, cmdname + "-log.txt"),
                              "Click for details", True)


def dummy_work(wdir, wloadname, cmdname):
  # Do the work of the child process here
  createdir(join(wdir, "parsed"))  # creating directory called parsed
  print "IP-addrs: ???"
  print "in child, sleeping"
  time.sleep(10000)
  return 0


def do_externalcmd(cmd):
  # subprocs = set()
  cmdstr = " ".join(cmd)
  print cmdstr
  signal.signal(signal.SIGINT, handle_signal)
  signal.signal(signal.SIGCHLD, signal.SIG_IGN)
  signal.signal(signal.SIGHUP, signal.SIG_IGN)
  proc = subprocess.Popen(cmd, shell=False,
                          preexec_fn=os.setsid,
                          close_fds=True, stdout=sys.stdout, stderr=sys.stderr)

  subprocs.add(proc)
  while proc.poll() is None:
    print "wlwizard child: awaiting subprocess to complete ..."
    proc.wait()
    # signal_children(subprocs, signal.SIGINT)
  print "wlwizard child: subprocess ended..."
  return 0


def do_parse(wdir, wloadname, cmdname, params):
  rawfiles = glob.glob("raw/*.raw")
  cfgfiles = glob.glob("raw/*[pP]rofile*.txt")
  objfiles = glob.glob("raw/*obj*graph*.txt")
  # try:
  cmd = [cmdpath("processdump.pl"), "-o", "."]
  if params.get('compact') == 'on':
    cmd.append("-compact")
  # if params.get('nocharts') == 'on':
  #        cmd.append("-nographs")
  #        #os._exit(0)
  if cfgfiles:
    profile = ["-cfg", ','.join(cfgfiles)]
    cmd.extend(profile)
  elif objfiles:
    objgraph = ["-obj", ','.join(objfiles)]
    cmd.extend(objgraph)
  cmd.extend(rawfiles)
  return do_externalcmd(cmd)


def do_capture(wdir, wloadname, cmdname, params):
  createdir(join(wdir, "raw"))  # creating raw directory so
  # this workload gets listed
  cmd = [cmdpath("wlcollect.pl"), "-o", "raw"]
  cmd.extend(params['ipaddrs'])
  return do_externalcmd(cmd)


def wlparse(params):
  wloadnames = params.get('wlnames').split(',')
  print "inside wlparse " + ",".join(wloadnames)
  response = []
  for w in wloadnames:
    wdir = join(repodir(), w)
    pidfile = join(wdir, "parse.pid")
    if os.path.exists(pidfile):
      response.append({"wlname": w,
                       "status": "Parsing in progress; skipped."})
    else:
      resp = fork_work(w, "parse", do_parse, params)
      print "return:", resp
      response.append({"wlname": w,
                       "status": resp})
  return response


def do_stop(w, cmdname, sig=signal.SIGINT):
  response = []
  pidfile = join(join(repodir(), w), cmdname + ".pid")
  print "pid:", pidfile
  if os.path.exists(pidfile):
    with open(pidfile) as f:
      pid = int(f.read())
      print "Stopping workload " + cmdname + " of " + w + " (pid " + str(pid) + ") ..."
      try:
        os.kill(pid, sig)
        # os.remove(pidfile)
        response.append({"wlname": w,
                         "status": cmdname + " stopped (process id " + str(pid) + ")"
                         })
      except Exception as e:
        print "Error: ", e
        print "pidfile path:", pidfile
        os.remove(pidfile)
  else:
    response.append({"wlname": w,
                     "status": cmdname + " not running."})
  return response


def wlcstop(args):
  wloadnames = args.get('wlnames').split(',')
  print "inside wlstop " + ",".join(wloadnames)
  response = []
  for w in wloadnames:
    response.extend(do_stop(w, "replay"))
    response.extend(do_stop(w, "capture"))
    response.extend(do_stop(w, "parse"))
  # print dumps(response,indent=4)
  return response


def wldelete(args):
  wloadnames = args.get('wlnames').split(',')
  wlcstop(args)
  response = []
  for w in wloadnames:
    print "inside wldelete " + w
    wdir = join(repodir(), w)
    try:
      if os.path.exists(wdir):
        print "deleting " + wdir
        shutil.rmtree(wdir)
        response.append({"wlname": w,
                         "status": "Success"})
    except Exception as e:
      print "Error in rmtree " + wdir + ": ", e
      response.append({"wlname": w, "status": "Failed: " + str(e)})
  # print dumps(response, indent=4)
  return response
