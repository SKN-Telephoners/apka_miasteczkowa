from backend import create_app
// Main entry point for the Flask application
// Po polsku: Główny punkt wejścia dla aplikacji Flask
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)