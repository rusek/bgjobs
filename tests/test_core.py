#!/usr/bin/env python

import os
import os.path
import unittest

import helpers

import bgjobs


class TestInitialization(unittest.TestCase):
    def setUp(self):
        self._temp_path = helpers.make_temp_dir()
        self._wp_path = os.path.join(self._temp_path, 'jobs')

    def test_auto_create(self):
        self.assertFalse(os.path.exists(self._wp_path))
        bgjobs.Workplace(self._wp_path)
        self.assertTrue(os.path.exists(self._wp_path))
        bgjobs.Workplace(self._wp_path)
        self.assertTrue(os.path.exists(self._wp_path))

    def test_force_create(self):
        bgjobs.Workplace(self._wp_path, create=True)
        self.assertTrue(os.path.exists(self._wp_path))
        self.assertRaises(bgjobs.BgjobsError, bgjobs.Workplace, self._wp_path, create=True)

    def test_no_create(self):
        self.assertRaises(bgjobs.BgjobsError, bgjobs.Workplace, self._wp_path, create=False)
        bgjobs.Workplace(self._wp_path)
        bgjobs.Workplace(self._wp_path, create=False)

    def test_create_with_existing_dir(self):
        os.mkdir(self._wp_path)
        self.assertRaises(bgjobs.BgjobsError, bgjobs.Workplace, self._wp_path, create=False)
        bgjobs.Workplace(self._wp_path, create=True)


class TestStartJob(unittest.TestCase):
    def setUp(self):
        self._temp_path = helpers.make_temp_dir()
        self._wp = bgjobs.Workplace(os.path.join(self._temp_path, 'jobs'))

    def test_success(self):
        job = helpers.wait_for_job(self._wp.start_job('exit 0'))
        self.assertEqual(job.get_status(), bgjobs.SUCCESS)
        self.assertEqual(job.get_retcode(), 0)

    def test_error(self):
        job = helpers.wait_for_job(self._wp.start_job('exit 7'))
        self.assertEqual(job.get_status(), bgjobs.ERROR)
        self.assertEqual(job.get_retcode(), 7)

    def test_stdout(self):
        job = helpers.wait_for_job(self._wp.start_job('echo msg'))
        self.assertEqual(helpers.read_file(job.stdout_path), 'msg\n')

    def test_stderr(self):
        job = helpers.wait_for_job(self._wp.start_job('echo msg >&2'))
        self.assertEqual(helpers.read_file(job.stderr_path), 'msg\n')

    def test_combine_stderr(self):
        cmd = 'echo first >&2 && echo second'
        job = helpers.wait_for_job(self._wp.start_job(cmd, combine_stderr=True))
        self.assertEqual(helpers.read_file(job.stdout_path), 'first\nsecond\n')
        self.assertEqual(helpers.read_file(job.stderr_path), '')

    def test_args_with_exit_shell_command(self):
        # exit is a shell built-in command, not a program
        job = helpers.wait_for_job(self._wp.start_job(['exit', '1']))
        self.assertEqual(job.get_status(), bgjobs.ERROR)

    def test_cwd(self):
        job = helpers.wait_for_job(self._wp.start_job('pwd'))
        self.assertEqual(helpers.read_file(job.stdout_path), job.path + '\n')

    def test_env_inheritance(self):
        with helpers.update_env(TEST_VALUE='abc'):
            job = helpers.wait_for_job(self._wp.start_job('echo $TEST_VALUE'))
        self.assertEqual(helpers.read_file(job.stdout_path), 'abc\n')

    def test_default_shell_label(self):
        job = self._wp.start_job('echo  "a b"')
        self.assertEqual(job.get_label(), 'echo  "a b"')
        helpers.wait_for_job(job)

    def test_default_args_label(self):
        job = self._wp.start_job(['echo', 'a b'])
        self.assertEqual(job.get_label(), 'echo \'a b\'')
        helpers.wait_for_job(job)

    def test_custom_label(self):
        job = self._wp.start_job('true', label='my label')
        self.assertEqual(job.get_label(), 'my label')
        helpers.wait_for_job(job)

    def test_unicode_label(self):
        job = self._wp.start_job('true', label=u'\u0119\u0105')
        self.assertEqual(job.get_label(), u'\u0119\u0105')
        helpers.wait_for_job(job)

if __name__ == '__main__':
    helpers.main()
