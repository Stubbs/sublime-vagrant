# Sublime-vagrant

## Implements common Vagrant commands.

- **Status:** Will show the status of this project's VM
- **Up:** Starts this project's VM
- **Halt:** Forcefully suspends the VM
- **Suspend:** Suspends the VM
- **Destroy:** Destroys the VM. Be careful, you won't be asked to confirm.
- **Destroy & Up:** Destroys the VM and starts it again. Useful for resetting to a known position.

## Settings

You can set up a different vagrant path if your Vagrant binary is not installed in the default location, or you're using Sublime-Vagrant on a windows machine.

```json
{
    "vagrant_path": "/usr/bin/vagrant",
    "additional_args": ['-h', '-v']
}
```

There are very few additional arguments you can pass to Vagrant so by default there are none in the setting file.

## Contributors
* https://github.com/Stubbs/ - Original Author
* https://github.com/benmatselby - For the code to execute runtime commands.
* https://github.com/NaleagDeco - Bug fixes & improvements
* https://github.com/jbrooksuk - Sublime Text 3 support
