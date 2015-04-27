# Sublime-vagrant

## Implements common Vagrant commands.

- **Init** Create a new Vagrantfile in the root directory of your project.
- **Status:** Will show the status of this project's VM
- **Up:** Starts this project's VM
- **Provision:** Runs configured provisioners
- **Halt:** Forcefully suspends the VM
- **Suspend:** Suspends the VM
- **Resume:** Resumes the VM
- **Reload:** Reloads Vagrantfile (equivalent to halt then up)
- **Destroy:** Destroys the VM. Be careful, you won't be asked to confirm.
- **Destroy & Up:** Destroys the VM and starts it again. Useful for resetting to a known position.
- **Rsync:** Rsync files from host to guest.

## Settings

You can set up a different vagrant path if your Vagrant binary is not installed in the default location, or you're using Sublime-Vagrant on a windows machine.

```json
{
    "vagrant_path": "/usr/bin/vagrant",
    "vagrantfile_path": "/vagrant",
    "additional_args": ['-h', '-v'],
    "output_to_window": true
}
```

By default Sublime-Vagrant will scan your first open folder and traverse up from there looking for a Vagrantfile, alternatively you may provide the "vagrantfile_path" setting which allows you to manually specify a relative path.

There are very few additional arguments you can pass to Vagrant so by default there are none in the setting file.

## Contributors
* https://github.com/Stubbs/ - Original Author
* https://github.com/benmatselby - For the code to execute runtime commands.
* https://github.com/NaleagDeco - Bug fixes & improvements
* https://github.com/jbrooksuk - Sublime Text 3 support
* https://github.com/arosolino - Bugfixes & missing Vagrant commands
* https://github.com/timcooper - Bugfixes & extra Vagrant commands
* https://github.com/fxdgear - pep8 and adding Rsync command

If you submit any bug fixes or improvements, don't forget to add yourself to the list of contributors.
