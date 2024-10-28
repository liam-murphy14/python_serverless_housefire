# Zero To 100 - Complete Guide to Adding a New Scraper

This guide is intended to help you get started with adding a new scraper to the Housefire platform. It assumes you have no experience with Nix, and very little Python experience. For a quick-start guide, see the [README](https://github.com/liam-murphy14/python_serverless_housefire). Since the people using this guide all have Mac, I will assume you are on a Mac, I will add instructions for other platforms later.

## 0. Prerequisites
First, locate the Terminal application on your computer. We will need it going forward, so add it to your dock or desktop for easy access.

We will need to install command line tools for your Terminal as well, go to [this link on the Apple website](https://download.developer.apple.com/Developer_Tools/Command_Line_Tools_for_Xcode_16/Command_Line_Tools_for_Xcode_16.dmg) to download the tools. You may need to restart your computer at some point during this process.

Once this is done, test it by running the following command in your terminal:

```bash
which clang
```

this should return something like `/usr/bin/clang`, if it gives you a message like `clang not found`, you may need to restart your computer.

## 1. Install Nix

Nix is how this project manages dependencies, and we will use it for this guide. One could alternatively install this project using the regular Python toolchain, but Nix simplifies the build process significantly for new users.

We will be using the [Determinate Systems Nix installer](https://zero-to-nix.com/concepts/nix-installer#:~:text=The%20Determinate%20Nix%20Installer%2C%20from,users%20to%20enable%20those%20features.) for our installation. To install Nix, run the following command in your terminal:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

Once this is done, quit and reopen the Terminal app. You should now have Nix installed on your computer. To test this, run the following command:

```bash
nix --version
```

This should return something like `nix (Nix) 2.3.10`, if it gives you a message like `nix not found`, you may need to restart your computer.

## 2. Set up the Housefire repository

### 2.1 Fork the repository and set up a GitHub account

We will be using GitHub to collaborate on this project. Go to [the project repository](https://github.com/liam-murphy14/python_serverless_housefire) and click the "Fork" button in the top right corner. This will create a copy of the repository in your GitHub account. If you do not yet have a GitHub account, you will need to create one.

### 2.2 Clone the repository to your computer

Next, we will install the GitHub command line tool, run the following command in your Terminal:

```bash
nix profile install nixpkgs#gh
```

Once this is installed, run `gh auth` and sign into your GitHub account. Then run `gh auth setup-git` to set up your git credentials.

Next, find your repository on GitHub (you can go to your account, then your repositories, then the Housefire one). Click the green "Code" button, click the "GitHub CLI" option, and copy the command that appears. Paste this command in your terminal and press Enter to run it.

Now, you will have a copy of the Housefire repo on your computer. Type `ls` in your terminal to see the files in the directory, you should see a folder called `python_serverless_housefire`. Run `cd python_serverless_housefire` to enter the directory.

### 2.3 Note on getting updates from the main repository

One more note, each time you want to add a new feature, you should go to your repository on GitHub and click `Sync Fork` to get the latest updates. Then, go to the Housefire repository with `cd python_serverless_housefire` and run `git pull` to get the latest updates.

## 3. Set up your development environment

Here, we are going to set up several tools that you will need to contribute code to this project.

### 3.1 Install shell tools

First, let's install Oh My Zsh, a tool that makes the terminal easier to use. Run the following command in your terminal:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

This will also make your terminal prettier. Don't be alarmed, everything will work the same.

We will be using the `direnv` tool to manage environment variables for the project. Run the following command in your terminal to install it:

```bash
nix profile install nixpkgs#direnv
```

Finally, we will set up Oh My Zsh to use direnv. Run the following command in your terminal:

```bash
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
```

### 3.2 Install Visual Studio Code

VSCode is the main code editor we will be using for the project. You can install [VSCode](https://code.visualstudio.com) by downloading from their website.

Once it is installed, open it and make sure everything looks good.

### 3.3 Configure VSCode

Next, we will install some extensions for VSCode. Click the Extensions button on the left side of the window, then search for and install the following extensions:

- Python by Microsoft
- Pylance by Microsoft
- direnv by Martin Kuhl

You will need to restart VSCode after installing these extensions.

### 3.4 Set up the project

Now, we will set up the project. First, restart your Terminal app to ensure everything is freshly loaded. Then, open a new Terminal window and navigate to the `python_serverless_housefire` directory with `cd python_serverless_housefire`. Then run the following command

```bash
direnv allow
```

This will allow direnv to set up the environment for the project. You should see a message like `direnv: loading .envrc` and it will take a while to install everything, maybe 2-3 minutes. Take a break and eat a snack, you have made it this far !!

Finally, once everything is set up, run the following command to set up the project:

```bash
nix run . -- init
```

You can press enter to use the default arguments most options. However, for the Google API key and Housefire API key, paste in the values that you got from me.

## 4. Add a new scraper

TODO
