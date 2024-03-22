# インストール￹方法￺ほうほう￻

　つかっているOSがFedoraかUbuntuであれば、かんたんに「ペイント」をインストールすることができます。

### Fedoraのばあい

　Fedora￹用￺よう￻のソフトウェア パッケージはCoprプロジェクト「[@esrille/releases](https://copr.fedorainfracloud.org/coprs/g/esrille/releases/)」から￹提供￺ていきょう￻しています。
このCoprプロジェクトを￹有効￺ゆうこう￻にするには、いちど、コマンドラインからつぎのように￹実行￺じっこう￻します。

```
sudo dnf copr enable @esrille/releases
```

　あとは、dnfコマンドで「ペイント」をインストールできます。

```
sudo dnf install esrille-paint
```

### Ubuntuのばあい

　Ubuntu￹用￺よう￻のソフトウェア パッケージはPPAレポジトリ「[esrille/releases](https://launchpad.net/~esrille/+archive/ubuntu/releases)」から￹提供￺ていきょう￻しています。
このPPAレポジトリを￹有効￺ゆうこう￻にするには、いちど、コマンドラインからつぎのように￹実行￺じっこう￻します。

```
sudo add-apt-repository ppa:esrille/releases
```

　あとは、aptコマンドで「ペイント」をインストールできます。

```
sudo apt update
sudo apt install esrille-paint
```

### ソースコードからインストールする￹方法￺ほうほう￻

　「ペイント」をソースコードからインストールしたいときは、つぎの￹手順￺てじゅん￻でインストールできます。

```
git clone https://github.com/esrille/paint.git
cd paint/
./autogen.sh --prefix=/usr
make
sudo make install
```

　ソースコードからビルドした「ペイント」をアンインストールするには、つぎのようにします:

```
sudo make uninstall
```
