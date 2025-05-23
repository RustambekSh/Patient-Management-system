# Advanced Patient Management System with AI Integration

A comprehensive healthcare management application that combines PostgreSQL database management with Google's Gemini AI for patient treatment suggestions and analysis.

## Features

- Complete patient management (add, view, update, delete)
- Appointment scheduling and tracking
- AI-powered treatment analysis and suggestions
- Medical history tracking
- Modern graphical user interface (PyQt6)
- Terminal interface option
- PostgreSQL database integration

## Screenshots

### Patient Management Tab
![Patient Management]()

### Treatment Analysis with AI
![AI Treatment Analysis]()

## Setup Requirements

1. PostgreSQL database server
2. Python 3.8+
3. Required Python packages (see requirements.txt)
4. Google Gemini API key (for AI features)

## Installation

1. Clone this repository
2. Install PostgreSQL if not already installed
3. Install required Python packages:

```
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:

```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
GEMINI_API_KEY=your_gemini_api_key
```

Alternatively, you can update the `config.json` file with your database configuration.

## Running the Application

There are two ways to run the application:

### Option 1: Using the launcher

Run the launcher script which allows you to choose between GUI and terminal interfaces:

```
python launcher.py
```

### Option 2: Direct launch

For the graphical user interface:
```
python app_gui.py
```

For the terminal interface:
```
python main.py
```

## Database Schema

The application uses the following tables:
- patients: Stores patient basic information
- appointments: Tracks scheduled appointments
- treatments: Records medical conditions and AI-generated treatment plans
- medical_history: Maintains a log of patient medical history

## AI Integration

The AI features use Google's Gemini API to:
1. Analyze patient symptoms
2. Generate treatment plan suggestions
3. Provide general health recommendations

Note: AI functionality requires a valid Gemini API key.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 