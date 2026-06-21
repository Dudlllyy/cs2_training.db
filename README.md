# CS2 Training Analyzer 🤖🎯

An automatic desktop tracker and training analyzer for Counter-Strike 2. The program works in real-time, eliminating the need to enter results manually. It intercepts system game logs, parses results from popular training maps, assigns efficiency grades, and saves the entire history to a local database.

## ✨ Key Features

* **Full Automation (Logging):** The script monitors changes in the `console.log` file in the background using multi-threading (`threading`), instantly extracting results right after completing an exercise.
* **Supports 7 Training Modes:**
  * `Speed` (Speed and KPS evaluation)
  * `Combat` (Round-based survival)
  * `Rush` (Holding off running bots)
  * `Flick`, `Blitz`, `Yuki`, `Multi`, `Strafe` (Point-based aim and tracking for score and accuracy)
* **Smart Grading System (Gamification):** The bot automatically calculates the completion percentage relative to your personal best (PB) and assigns color markers:
  * 🟩 **Excellent** (>= 90% of the record or a new PB)
  * 🟨 **Normal** (75% - 89% of the record)
  * 🟥 **Bad** (< 75% of the record)
* **Long-term Memory (SQLite):** All session results and detailed reports for each round are saved in the local database file `cs2_stats.db`.
* **Progress Comparison:** Upon finishing a session, the program compares your current results with the previous training day and clearly shows if your form is improving.
* **Auto-clearing Logs:** After summarizing the results, the program automatically clears the heavy CS2 log file, saving disk space.
* **Modern GUI:** The application interface is built with a dark theme using the `CustomTkinter` library.

## 🛠 Tech Stack

* **Language:** Python 3.x
* **Interface:** CustomTkinter (Dark theme)
* **Database:** SQLite3
* **Data Parsing:** Multi-threading (`threading`) + Regular expressions (`re`)
* **Project Build:** PyInstaller

## 🚀 Setup and Launch

### 1. Preparing Counter-Strike 2
For the game to write its logs to a text file, you need to enable debugging mode in Steam:
1. Open your Steam library and go to the **Properties** of Counter-Strike 2.
2. In the **General** tab, find the **Launch Options** field.
3. Add the command with a space: `-condebug`

### 2. Installing Dependencies
The application requires external UI libraries. Install them using the package manager:

bash
uv pip install customtkinter


### 3. Running the Script
Ensure the correct path to your `console.log` file inside the Steam folder is specified in the code. Then, run the application:

bash
python main.py


## 📦 Building a Standalone .exe File

If you want to use the application without having Python installed, as a regular Windows program, build it using `PyInstaller`.

1. Install the builder:
   bash
   uv pip install pyinstaller
   
2. Run the build command in the project folder:
   bash
   pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter main.py
   
3. The compiled `main.exe` file will appear in the `dist` folder. Move it one level up (next to the `cs2_stats.db` database file), create a shortcut on your Desktop, and launch it with a single click.

## 📝 Database Structure

The program uses two linked tables:
* `sessions` — stores the training date and the total number of grades (Good/Normal/Bad) for the day.
* `results` — stores specific results for each played mode, linked to a specific session.
