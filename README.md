# [ CROSTINI TOOLBOX ]

## OVERVIEW
> Tactical automation scripts for Debian (Crostini). No bloat, no fluff—just stable deployments and system maintenance.

## THE TOOLKIT

### 1. wp_installer.sh
**Function:** Deploys a full WordPress stack (LAMP/LEMP).
**Intel:** * Automates database creation and user permissions.
* Configures PHP-FPM and web server blocks.
* Best used on a fresh container to avoid port conflicts.

### 2. sys_clean.sh
**Function:** System hardening and maintenance.
**Intel:**
* Clears out APT caches and orphaned packages.
* Removes temporary logs that eat up shared ChromeOS storage.
* Runs a quick check on disk usage.

### 3. git_setup.sh
**Function:** Identity configuration.
**Intel:**
* Quickly sets user.name and user.email.
* Generates an Ed25519 SSH key if one isn't detected.
* Links to the GitHub clipboard for easy bootstrapping.

## DEPLOYMENT
$ git clone https://github.com/user/crostini-toolbox.git
$ cd crostini-toolbox
$ chmod +x scripts/*.sh

## USAGE
Run scripts directly from the scripts directory:
$ ./scripts/wp_installer.sh

--
[ 198X-202X ] // STABILITY OVER NOISE
