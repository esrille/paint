# Installing Paint

If you are using Fedora or Ubuntu, you can install **Paint** with just a few commands in your terminal.

## Fedora

The **Paint** software package is provided through the [@esrille/releases](https://copr.fedorainfracloud.org/coprs/g/esrille/releases/) Copr project.
To enable this Copr project, execute the following command:

```
sudo dnf copr enable @esrille/releases
```

After enabling the Copr project, install the **Paint** package using the following command:

```
sudo dnf install esrille-paint
```

## Ubuntu

The **Paint** software package is provided from the [esrille/releases](https://launchpad.net/~esrille/+archive/ubuntu/releases) PPA repository.
To enable this PPA repository, execute the following commands:

```
sudo add-apt-repository ppa:esrille/releases
sudo apt update
```

After updating the PPA repositories, install the **Paint** package using the following command:

```
sudo apt install esrille-paint
```

## Building Sources

To build and install **Paint** manually, run the following commands:

```
git clone https://github.com/esrille/paint.git
./autogen.sh --prefix=/usr
make
sudo make install
```

To uninstall **Paint**, run the following command:

```
sudo make uninstall
```
