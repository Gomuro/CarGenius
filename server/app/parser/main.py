from server.app.parser.logic.test_open_driver import open_driver

if __name__ == "__main__":
    try:
        open_driver()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        print("Script finished")
