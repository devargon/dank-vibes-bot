<p align="center">
  <a href="https://www.python.org/downloads/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/Red-Discordbot">
  </a>
  <a href="https://github.com/Rapptz/discord.py/">
     <img src="https://img.shields.io/badge/discord-py-blue.svg" alt="discord.py">
  </a>
</p>

# Dank Vibes Bot

This is the repository for the bot used in Dank Vibes, a Dank Memer partnered server. How tf did you get here btw

## How to setup
### Prerequisites
 - Git
 - Python 3.6+
 - Dank Vibes Bot uses discord.py (2.0.0a) to make use of interaction features such as buttons.
 - Dank Vibes Bot uses PostgreSQL for all database needs.

### Instructions

1. Install PostgreSQL on your machine. You can do so with these guides for [Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-postgresql-on-ubuntu-20-04-quickstart), and for [Windows and Mac](https://www.enterprisedb.com/docs/supported-open-source/postgresql/installer/02_installing_postgresql_with_the_graphical_installation_wizard/).
   - You can find download links for PostgreSQL installation [here](https://www.postgresql.org/download/).
2. Clone this repository to a directory of your choice and install the [requirements](requirements.txt).
3. You should have created an account for the bot to access the database with both read and write permissions. You should not use the inbuilt superuser account as this is not recommended due to security issues.
4. Create a database in the PostgreSQL server. It can easily be done with the [pgAdmin](https://www.pgadmin.org/) tool on Windows and Mac. For operating systems like Ubuntu, you can use [this guide](https://www.liquidweb.com/kb/creating-and-deleting-a-postgresql-database/).  
5. Head over to GitHub's [Personal Access Tokens](https://github.com/settings/tokens), and generate a new token with **no expiration date**, and grant it the `repo`, `read:repo_hook` and `read:user` scopes. They are needed for the bot to access the `github` command, which directly fetches information from the [GitHub REST API](https://docs.github.com/en/rest). ![The scopes required](https://cdn.nogra.xyz/screenshots/brave_IV8Gh9rXgt.png)
6. Create a file called `credentials.env`.

   1. In the file, add the following lines:
   ```
   TOKEN=Your Discord bot's token
   HOST=127.0.0.1 (if you're testing your bot with a local database)
   DATABASE=The name of the database in the PostgreSQL server.
   dbUSER=The username you set for the bot to access the PostgreSQL server.
   dbPASSWORD=The password you set for the bot to access the PostgreSQL server.
   GITHUBPAT = The GitHub personal access token you generated in step 5
   state = 1 (anything other than above 1 means the bot is the development version)
   tenorAPI= your tenor API key
   bugsnap_key = Your bugsnap key
   AMARI_KEY = Your Amari Developer Key
   ```
9. Start the bot.
   - On the first run, the bot should create all the databases needed. Some errors might pop up here and there, after a few restarts it should work. 
   - Some data is required in order for the bot to work. DM Argon if there are unexpected errors.
