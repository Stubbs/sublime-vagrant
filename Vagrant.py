import sublime
import sublime_plugin
import subprocess
import os
import functools
import time
import sys
from os.path import exists, isdir, dirname
try:
    import thread
except ImportError:
    import _thread as thread  # Py3K changed it.


class PrefsMeta(type):
    def __init__(self, class_name, bases, namespace):
        self.settings = None
        self.validVagrantfilePath = False
        self.default = {
            'vagrant_path': "/usr/bin/vagrant",
            'vagrantfile_path': "",
            'additional_args': {},
            'debug': False,
            'output_to_window': False
        }

    def __getattr__(self, attr):
        if(self.settings is None):
            self.settings = sublime.load_settings('Vagrant.sublime-settings')

        return self.settings.get(attr, None if attr not in self.default else self.default[attr])

    def get_vagrantfile_path(self):
        if self.validVagrantfilePath:
            return self.validVagrantfilePath
        else:
            window = sublime.active_window()
            folder = window.folders()[0]
            vagrantfile_path = Prefs.vagrantfile_path

            if vagrantfile_path and exists(folder + vagrantfile_path + "/Vagrantfile"):
                self.validVagrantfilePath = folder + vagrantfile_path
                return self.validVagrantfilePath

            if exists(vagrantfile_path + "/Vagrantfile"):
                self.validVagrantfilePath = vagrantfile_path
                return self.validVagrantfilePath

            found = False

            while not found:
                print("Searching : " + folder)

                if exists(folder + "/Vagrantfile"):
                    self.validVagrantfilePath = folder
                    return self.validVagrantfilePath

                # If this directory has the git folder, stop.
                if exists(folder + "/.git") and isdir(folder + "/.git"):
                    print('Unable to find Vagrantfile, found .git folder and assumed this is the root of your project.')
                    raise Exception("Unable to find Vagrantfile, found .git folder and assumed this is the root of your project.")

                # Have we hit rock bottom?
                if dirname(folder) == folder:
                    print('Unable to find root folder, sublime-vagrant only supports git right now.')
                    raise Exception("Unable to find root folder, sublime-vagrant only supports git right now.")

                # Try the next directory up.
                folder = dirname(folder)

Prefs = PrefsMeta('Prefs', (object, ), {})


# StatusProcess cribbed from:
# https://github.com/stuartherbert/sublime-phpunit/blob/master/phpunit.py
class StatusProcess(object):
    def __init__(self, msg, listener):
        self.msg = msg
        self.listener = listener
        thread.start_new_thread(self.run_thread, ())

    def run_thread(self):
        progress = ""
        while True:
            if self.listener.is_running:
                if len(progress) >= 10:
                    progress = ""
                progress += "."
                sublime.set_timeout(functools.partial(self.listener.update_status, self.msg, progress), 0)
                time.sleep(1)
            else:
                break


# the AsyncProcess class has been cribbed from:
# https://github.com/stuartherbert/sublime-phpunit/blob/master/phpunit.py
# and in turn: https://github.com/maltize/sublime-text-2-ruby-tests/blob/master/run_ruby_test.py
class AsyncProcess(object):
    def __init__(self, cmd, cwd, listener):
        self.listener = listener

        if os.name == 'nt':
            # we have to run PHPUnit via the shell to get it to work for everyone on Windows
            # no idea why :(
            # I'm sure this will prove to be a terrible idea
            self.proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        else:
            # Popen works properly on OSX and Linux
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        if self.proc.stdout:
            thread.start_new_thread(self.read_stdout, ())
        if self.proc.stderr:
            thread.start_new_thread(self.read_stderr, ())

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2 ** 15)
            if data:
                sublime.set_timeout(functools.partial(self.listener.append_line, data), 0)
            else:
                self.proc.stdout.close()
                self.listener.is_running = False
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2 ** 15)
            if data:
                sublime.set_timeout(functools.partial(self.listener.append_line, data), 0)
            else:
                self.proc.stderr.close()
                self.listener.is_running = False

                break


class ShellCommand(object):
    """Base class for shelling out a command to the terminal"""
    def __init__(self):
        self.error_list = []
        self.vagrantConfigPath = Prefs.get_vagrantfile_path()
        self.output_view = None
        self.output_messages = ""

    def get_errors(self, path):
        self.execute(path)
        return self.error_list

    def append_line(self, message):
        message_str = message.decode(sys.getdefaultencoding()).strip()
        if message_str != "":
            self.output_messages += message_str + "\n"

            # Print to the console
            print(message_str)

            if Prefs.output_to_window == True:
                # Print to the window if configured
                self.output_view.run_command('vagrant_output', {'console_output': self.output_messages})

    def shell_out(self, cmd):
        try:
            data = None
            print(' '.join(cmd))

            shell = sublime.platform() == "windows"
            proc = subprocess.Popen(cmd, cwd=self.vagrantConfigPath, stdout=subprocess.PIPE, shell=shell, stderr=subprocess.STDOUT)

            if proc.stdout:
                data = proc.communicate()[0]

            return (proc.returncode, data)
        except OSError as e:
            print('OS Error. (' + e.errno + " : " + e.strerror + ')')

    def update_status(self, msg, progress):
        sublime.status_message(msg + " " + progress)

    def start_async(self, caption, executable, cwd):
        self.is_running = True
        self.proc = AsyncProcess(executable, cwd, self)
        StatusProcess(caption, self)

    def run_command(self, command, params={}, async=True):
        args = []

        application_path = Prefs.vagrant_path

        args = [application_path]

        args.append(command)

        # Check for any extra args the user wants to include.
        for key, value in Prefs.additional_args.items():
            arg = key
            if value != "":
                arg += "=" + value
            args.append(arg)

        for key, value in params.items():
            arg = key

            if value != "":
                arg += "=" + value

            args.append(arg)

        print(' '.join(args))

        if Prefs.output_to_window == True:
            self.output_view = sublime.active_window().new_file();
            self.output_messages = 'Vagrant Command: ' + ' '.join(args) + "\n\n"

        if async:
            self.start_async("Running Vagrant ", args, self.vagrantConfigPath)
        else:
            (returncode, data) = self.shell_out(args)
            print(data)
            return returncode

    def execute(self, path=''):
        #debug_message('Command not implemented')
        print('Command not implemented')


class Vagrant(ShellCommand):

    def __init__(self):
        super(Vagrant, self).__init__()

class VagrantReload(Vagrant):
    def execute(self, path=''):
        self.run_command('reload')


class VagrantDestroy(Vagrant):
    def execute(self, path=''):
        self.run_command('destroy', {'--force': ''})


class VagrantUp(Vagrant):
    def execute(self, path=''):
        self.run_command('up')


class VagrantStatus(Vagrant):
    def execute(self, path=''):
        self.run_command('status')


class VagrantDestroyUp(Vagrant):
    def execute(self, path=''):
        result = self.run_command('destroy', {'--force': ''}, False)
        if result == 0:
            self.run_command('up')


class VagrantInit(Vagrant):
    def execute(self, path=''):
        self.run_command('init')


class VagrantHalt(Vagrant):
    def execute(self, path=''):
        self.run_command('halt')


class VagrantSuspend(Vagrant):
    def execute(self, path=''):
        self.run_command('suspend')


class VagrantProvision(Vagrant):
    def execute(self, path=''):
        self.run_command('provision')


class VagrantResume(Vagrant):
    def execute(self, path=''):
        self.run_command('resume')


class VagrantRsync(Vagrant):
    def execute(self, path=''):
        self.run_command('rsync')


class VagrantBaseCommand(sublime_plugin.TextCommand):
    def run(self, paths=[]):
        print("Not implemented")

    def is_enabled(self):
        try:
            path = Prefs.get_vagrantfile_path()

            if Prefs.debug:
                print('Vagrant config path found: ' + path)
        except Exception:
            return False

        return True


class VagrantReloadCommand(VagrantBaseCommand):
    description = 'Reload the Vagrant VM.'

    def run(self, args):
        '''Reload the Vagrant config for this VM'''
        cmd = VagrantReload()
        cmd.execute()

    def description(self):
        return 'Reload the Vagrant config.'


class VagrantDestroyCommand(VagrantBaseCommand):
    description = 'Destroy the Vagrant VM.'

    def run(self, args):
        '''Destroy the Vagrant config for this VM'''
        cmd = VagrantDestroy()
        cmd.execute()

    def description(self):
        return 'Destroy the Vagrant config.'


class VagrantUpCommand(VagrantBaseCommand):
    description = 'Start the Vagrant VM.'

    def run(self, args):
        '''Start the Vagrant config for this VM'''
        cmd = VagrantUp()
        cmd.execute()

    def description(self):
        return 'Start the Vagrant VM.'


class VagrantDestroyUpCommand(VagrantBaseCommand):
    description = 'Destroy & Start the Vagrant VM.'

    def run(self, args):
        '''Reload the Vagrant config for this VM'''
        cmd = VagrantDestroyUp()
        cmd.execute()

    def description(self):
        return 'Reload the Vagrant config.'


class VagrantHaltCommand(VagrantBaseCommand):
    description = 'Forcefully halt the Vagrant VM.'

    def run(self, args):
        '''Reload the Vagrant config for this VM'''
        cmd = VagrantHalt()
        cmd.execute()

    def description(self):
        return 'Forcefully halt the Vagrant VM.'


class VagrantSuspendCommand(VagrantBaseCommand):
    description = 'Suspend the Vagrant VM.'

    def run(self, args):
        '''Reload the Vagrant config for this VM'''
        cmd = VagrantSuspend()
        cmd.execute()

    def description(self):
        return 'Suspend the Vagrant VM.'


class VagrantStatusCommand(VagrantBaseCommand):
    description = 'Status of the Vagrant VM.'

    def run(self, args):
        '''Reload the Vagrant config for this VM'''
        cmd = VagrantStatus()
        cmd.execute()

    def description(self):
        return 'Status of the Vagrant VM.'


class VagrantProvisionCommand(VagrantBaseCommand):
    description = 'Run any configured Vagrant provisioners.'

    def run(self, args):
        '''Run the configured provisioner configured on this VM'''
        cmd = VagrantProvision()
        cmd.execute()


class VagrantResumeCommand(VagrantBaseCommand):
    description = 'Resume the Vagrant VM.'

    def run(self, args):
        '''Reload the Vagrant config for this VM'''
        cmd = VagrantResume()
        cmd.execute()

    def description(self):
        return 'Resume the Vagrant VM.'


class VagrantInitCommand(VagrantBaseCommand):
    description = 'Initialise a new Vagrant project.'

    def run(self, args):
        '''Start the Vagrant config for this VM'''
        cmd = VagrantInit()
        cmd.execute()

    def is_enabled(self):
        return True

    def description(self):
        return 'Initialise a new Vagrant project.'


class VagrantRsyncCommand(VagrantBaseCommand):
    description = 'Rsync files from host machine to guest machine'

    def run(self, args):
        '''Rsyncing Files'''
        cmd = VagrantRsync()
        cmd.execute()

    def is_enabled(self):
        return True

    def description(self):
        return 'Rsync files from host machine to guest machine.'


class VagrantOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        sizeBefore = self.view.size()
        self.view.insert(edit, sizeBefore, args.get('console_output')[sizeBefore:])
        self.view.show(self.view.size())
