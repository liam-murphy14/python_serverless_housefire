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

Once this is installed, run `gh auth login` and sign into your GitHub account. Then run `gh auth setup-git` to set up your git credentials.

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

Now, we will go through the steps to add a new scraper to the project.

### 4.1 Open the project in VSCode

Open VSCode and click the "Open Folder" button. Navigate to the `python_serverless_housefire` directory and click "Open". You should see the project files on the left side of the window.

Now, open the `cli.py` file. At the top of the file, check if the import statements have any errors or warnings associated with them. If they do, click the tab in the bottom right corner of VSCode that says `Python 3.9.12` or something similar. Click the `Select Interpreter` option, then select the option with a long string of random characters in front of it. This should fix the errors.

### 4.2 A note on project structure

This project is designed as a CLI with 3 steps. You can think of it as a pipeline (and the combo command is aptly named `run-data-pipeline`). First is the `scrape` step, which scrapes data from a website. Second is the `transform` step, which transforms the data into a format that can be used by the Housefire platform. Third is the `upload` step, which loads the data into the Housefire web platform.

For the purposes of this guide, we will be focusing on the `scrape` step primarily, and the `transform` step secondarily.

You can find the existing scrapers in the `scraper` directory. Each scraper is a Python class that inherits from the `Scraper` class in `scraper.py`, and is instantiated by the `ScraperFactory` class in `scraper_factory.py`. Each scraper has to implement the `execute_scrape` method, as well as the `debug_scrape` method. The `execute_scrape` method is the main method that is called when the scraper is run, and the `debug_scrape` method is used for debugging/testing purposes.

Each actual scraper is organized by the REIT ticket name in the `reits_by_ticker` directory, and is named `[Ticker]Scraper`. See the `pld.py` scraper for an example.

### 4.3 Add a new scraper

First, choose a REIT to scrape data for. You can find a list of largest REITs by market cap [here](https://companiesmarketcap.com/reit/largest-reits-by-market-cap/).

Once you have chosen a ticker, add a new file named `<ticker>.py` to the `reits_by_ticker` directory. Add the following content to the file.

```python
import nodriver as uc
import pandas as pd
from housefire.scraper.scraper import Scraper


class <Ticker>Scraper(Scraper):
    def __init__(self):
        super().__init__()

    async def execute_scrape(self) -> pd.DataFrame:
        start_url = "EXAMPLEURL"
        tab = await self.driver.get(start_url)
        return pd.DataFrame()

    async def _debug_scrape(self):
        self.logger.debug("Debugging the <ticker> scraper")
```

Replacing `<Ticker>` and `<ticker>` with the ticker (following the capitalization) of the REIT you have chosen. Replace `EXAMPLEURL` with the URL of the website you will be scraping data from. Typically this will be the REIT website.

Using the `uc` library, you can interact with the website to scrape data. The `self.driver` object is an instance of the `uc` library that you can use to interact with the website. You can find the documentation for the `uc` library [here](https://ultrafunkamsterdam.github.io/nodriver/). You can also look at the existing scrapers for examples of how to use the `uc` library.

Basically, you will add code to the `execute_scrape` method that will scrape data from the website and return it as a Pandas DataFrame (like a spreadsheet for Python).

### 4.4 Add the scraper to the factory

Next, open the `scraper_factory.py` file. Add an import statement for your new scraper at the top of the file, like so:

```python
from housefire.scraper.reits_by_ticker.<ticker> import <Ticker>Scraper
```

Next, add your new scraper to the `self.scraper_map` dictionary in the `ScraperFactory` class, similar to the existing scrapers.

### 4.5 An aside: what data we want to collect

In order to write your scraper effectively, we need to know what kind of data we want. For the first iteration of the project, we want property data for each REIT. This includes the property name, address, and square footage of each property that the REIT owns (see our [Housefire data model](https://github.com/liam-murphy14/svelte_app_housefire/blob/1f293334350ab04eb35b21433f813fa71f85e7d1/prisma/schema.prisma#L23) for details).

First, see what the website has available. Many REIT websites have a webpage where you can view all properties that they own. If you cannot get every piece of data we need from this website, don't worry, we can also get additional data during the transform step. For the scraper, just focus on getting the name, plus enough information so that we can look up the property on Google Maps and identify it.

### 4.6 Test your scraper

Now, you can test your scraper by running the following command in your terminal:

```bash
nix run . -- scrape --debug <ticker>
```

This will run the `debug_scrape` method of your scraper, which is useful for testing and debugging. You can also run the `execute_scrape` method by running the following command:

```bash
THIS CURRENTLY DOES NOT WORK, WILL FIX
```

### 4.7 Add a transformer

Once the scraper is returning the right data, we need to add a transformer to let the full data pipeline run. In either case, we need to add a new transformer file for the new REIT, named `<ticker>.py` in the `transform/reits_by_ticker` folder, and adding it to the `transformer_factory.py` file (similar to adding our scraper to the `scraper_factory`). For our purposes, we will do 2 things:

1. If we don't have the full address of the property, we will use the Google Maps API to get the full address. For this, create a geocode transformer by following the example of `eqix.py` in the `transform/reits_by_ticker` folder. This allows us to automatically get the full address of the property.
2. If we collected the square footage, we will convert it to a number by adding the following line to the `execute_transform` method: `data["squareFootage"] = data["squareFootage"].apply(self.parse_area_string)`.
