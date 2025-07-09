#!/usr/bin/env python3

from app import create_app


def main() -> None:
    try:
        app = create_app()
        
        app.root.mainloop()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Fatal error in the application: {e}")
        raise


if __name__ == "__main__":
    main()
