import errno
import fcntl
import os
import os.path
import pipes
import signal
import shutil
import subprocess
import time


def _preexec_detach():
    os.setsid()

    pid = os.fork()
    if pid > 0:
        os._exit(0)

    os.umask(0)


class WorkplaceBackend(object):
    def __init__(self, path):
        self._path = path

    def get_path(self):
        return self._path

    def get_job_path(self, job_id):
        return os.path.join(self._path, str(job_id))

    def exists(self):
        return os.path.exists(self._get_job_counter_path())

    def init(self):
        try:
            os.makedirs(self._path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        for job_id in self.iter_all_jobs():
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST), str(job_id))

        with open(self._get_job_counter_path(), 'w') as f:
            f.write('1\n')

    def job_exists(self, job_id):
        return os.path.exists(self.get_job_path(job_id))

    def init_job(self):
        job_id = self._next_job_id()
        os.mkdir(self.get_job_path(job_id))
        return job_id

    def start_job(self, job_id, cmd, combine_stderr):
        self._write_job_cmd(job_id, cmd)
        self._run_job_cmd(job_id, combine_stderr)

    def is_job_running(self, job_id):
        return self._is_job_running_by_pid(job_id, self._get_job_pid(job_id))

    def get_job_retcode(self, job_id):
        try:
            with open(os.path.join(self.get_job_path(job_id), 'job_retcode')) as f:
                return int(f.read())
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            return None

    def kill_job(self, job_id):
        pid = self._get_job_pid(job_id)
        if self._is_job_running_by_pid(job_id, pid):
            os.killpg(os.getpgid(pid), signal.SIGKILL)

    def destroy_job(self, job_id):
        shutil.rmtree(self.get_job_path(job_id))

    def iter_all_jobs(self):
        for entry in os.listdir(self._path):
            if entry.isdigit():
                yield int(entry)

    def _get_job_counter_path(self):
        return os.path.join(self._path, '.bgjobs_counter')

    def _write_job_cmd(self, job_id, cmd):
        if isinstance(cmd, basestring):
            cmd = ['/bin/sh', '-c', cmd]

        job_path = self.get_job_path(job_id)

        with open(os.path.join(job_path, 'job_cmd'), 'w') as f:
            f.write(
                'echo $$ > job_pid\n'
                '({cmd})\n'
                'echo $? > job_retcode\n'.format(
                    cmd=' '.join(map(pipes.quote, cmd)),
                    path=job_path,
                )
            )

    def _run_job_cmd(self, job_id, combine_stderr):
        job_path = os.path.join(self._path, str(job_id))

        with open('/dev/null', 'r') as stdin:
            with open(os.path.join(job_path, 'job_out'), 'w') as stdout:
                with open(os.path.join(job_path, 'job_err'), 'w') as stderr:
                    if combine_stderr:
                        # still, job_err should be created
                        stderr = stdout
                    subprocess.check_call(
                        self._get_run_args(job_id),
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr,
                        close_fds=True,
                        preexec_fn=_preexec_detach,
                        cwd=job_path,
                    )

        pid_path = os.path.join(job_path, 'job_pid')
        for i in xrange(1000):
            if os.path.exists(pid_path):
                break
            time.sleep(0.01)

    def _get_run_args(self, job_id):
        return ['/bin/sh', os.path.join(self.get_job_path(job_id), 'job_cmd')]

    def _get_job_pid(self, job_id):
        pid_path = os.path.join(self.get_job_path(job_id), 'job_pid')
        with open(pid_path) as f:
            pid = int(f.read())
        if pid <= 0:
            raise ValueError('Invalid pid: {0!r}'.format(pid))
        return pid

    def _is_job_running_by_pid(self, job_id, pid):
        try:
            with open('/proc/{0}/cmdline'.format(pid)) as f:
                cmdline = f.read()
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            return False

        return cmdline == '\0'.join(self._get_run_args(job_id)) + '\0'

    def _next_job_id(self):
        with open(self._get_job_counter_path(), 'r+') as f:
            fcntl.lockf(f.fileno(), fcntl.LOCK_EX)
            job_id = int(f.read())
            f.seek(0)
            f.truncate(0)
            f.write('{0}\n'.format(job_id + 1))
        return job_id
