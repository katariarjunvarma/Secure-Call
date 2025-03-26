from app import app

# Entry point of the application
if __name__ == "__main__":
    # Run the application
    # Ensure debug mode is only enabled in development
    app.run(host="0.0.0.0", port=5000, debug=True)  # Set debug=False in production