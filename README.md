# [ CROSTINI TOOLBOX ]

## OVERVIEW
> Tactical automation and development utilities for Debian (Crostini). Built for stability, speed, and clean deployments.

## THE TOOLKIT

### 📂 /scripts (Executable Utilities)
* **wp_installer.sh** Deploys a full WordPress stack (LAMP/LEMP) on a fresh container. Automates DB creation and PHP-FPM configuration.
* **list_openai_models.sh** Quick utility to query OpenAI for available models. Requires `OPENAI_API_KEY` in `.env`.
* **get_gemini_models.sh** Queries Google AI Studio for detailed Gemini model specs (Input/Output limits, etc.). Requires `GEMINI_API_KEY` in `.env`.

### 📂 /apps (Python/Streamlit Applications)
* **article_generator.py** A "One-Shot" SEO Article Generator (V4). Features XML system prompts and WordPress "Ghost Image" support.

### 📂 /snippets (WordPress & PHP Logic)
* **visual-term-editor.php** Enables TinyMCE Visual Editor for Category and Tag descriptions.
* **enable-app-passwords.php** Forces Application Passwords availability on insecure (HTTP) connections.

## DEPLOYMENT
$ git clone https://github.com/BashDEV96/crostini-toolbox.git
$ cd crostini-toolbox
$ chmod +x scripts/*.sh

## CONFIGURATION
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY="your_key_here"
GEMINI_API_KEY="your_key_here"
```

--
[ 198X-202X ] // STABILITY OVER NOISE
