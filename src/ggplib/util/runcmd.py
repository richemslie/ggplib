from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen
from ggplib.util import log


class Alarm(Exception):
    pass


def alarm_handler(signum, frame):
    raise Alarm()


def run(args, verbose=False, cwd=None, shell=False, kill_tree=True, timeout=-1, env=None):
    ' Run a command with a timeout after which it will be forcibly killed. '

    p = Popen(args, shell=shell, cwd=cwd, stdout=PIPE, stderr=PIPE, env=env)

    if timeout != -1:
        signal(SIGALRM, alarm_handler)
        alarm(timeout)

    try:
        stdout, stderr = p.communicate()
        if verbose:
            print stdout, stderr

        if timeout != -1:
            alarm(0)

    except Alarm, e:
        log.warning("Alarm triggered: %s" % e)
        pids = [p.pid]

        if kill_tree:
            pids.extend(get_process_children(p.pid))

        for pid in pids:
            # process might have died before getting to this line
            # so wrap to avoid OSError: no such process
            try:
                log.warning("killing %s" % pid)
                kill(pid, SIGKILL)
            except OSError:
                pass

        return -9, '', ''

    return p.returncode, stdout, stderr


def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return [int(c) for c in stdout.split()]


###############################################################################

if __name__ == '__main__':
    import pprint
    pprint.pprint(run('find /', shell=True, timeout=1))
    pprint.pprint(run('find', shell=True))
