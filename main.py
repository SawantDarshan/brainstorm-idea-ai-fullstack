# Main entry point - select interface to run
import sys

def main():
    from config.global_context import APP_MODE
    mode = sys.argv[1] if len(sys.argv) > 1 else APP_MODE

    if mode == "cli":
        from interfaces.cli.cli_app import main as cli_main
        cli_main()
    elif mode == "api":
        from interfaces.api.api_app import start as api_start
        api_start()
    elif mode == "web":
        from interfaces.api.api_app import start as api_start
        api_start()
    else:
        print(f"Unknown mode: {mode}. Use 'cli', 'api', or 'web'.")

if __name__ == "__main__":
    main()