import os.path

from .backend import WorkplaceBackend
from .error import BgjobsError


class Workplace(object):
    def __init__(self, path, create=None):
        self._backend = WorkplaceBackend(path)
        if self._backend.exists():
            if create is True:
                raise BgjobsError('Workplace already exists')
        else:
            if create is False:
                raise BgjobsError('Workplace does not exist')
            self._backend.init()

    @property
    def path(self):
        return self._backend.get_path()

    def start_job(self, cmd, combine_stderr=False):
        job_id = self._backend.init_job()
        self._backend.start_job(job_id, cmd, combine_stderr)
        return Job(self._backend, job_id)

    def get_job(self, job_id):
        if self._backend.job_exists(job_id):
            return Job(self._backend, job_id)
        else:
            raise BgjobsError('Job does not exist')

    def clean(self):
        for job_id in self._backend.iter_all_jobs():
            if not self._backend.is_job_running(job_id):
                self._backend.destroy_job(job_id)

    def __iter__(self):
        for job_id in sorted(self._backend.iter_all_jobs()):
            yield Job(self._backend, job_id)


class Job(object):
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    DEAD = 'dead'

    def __init__(self, backend, job_id):
        self._backend = backend
        self._job_id = job_id

    @property
    def id(self):
        return self._job_id

    @property
    def path(self):
        return self._backend.get_job_path(self._job_id)

    @property
    def stdout_path(self):
        return os.path.join(self._backend.get_job_path(self._job_id), 'job_out')

    @property
    def stderr_path(self):
        return os.path.join(self._backend.get_job_path(self._job_id), 'job_err')

    def is_running(self):
        return self._backend.is_job_running(self._job_id)

    def get_status(self):
        if self._backend.is_job_running(self._job_id):
            return self.RUNNING
        else:
            retcode = self._backend.get_job_retcode(self._job_id)
            if retcode is None:
                return self.DEAD
            elif retcode == 0:
                return self.SUCCESS
            else:
                return self.ERROR

    def get_retcode(self):
        return self._backend.get_job_retcode(self._job_id)

    def kill(self):
        return self._backend.kill_job(self._job_id)
