## Course Seat Bot
Notifies whenever a new seat opens up in a particular course.

#### Setup
- Virtual environment for packages: `python3 -m venv .venv`
- Install dependencies: `pip install -r requirements.txt`
- Place token in a new `.env` file, should contain one line like `TOKEN=...`

#### Usage
- `$set_channel` - choose channel for bot to report in
- `$add_class url` - monitor url
- `$set_refresh mins` - change refresh rate (default 5)  
