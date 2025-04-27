
import sys
import os

def show_welcome():
    """Display welcome message and options"""
    print("\n" + "="*60)
    print("   Advanced Patient Management System - Green Edition   ")
    print("   With AI Integration & Modern UI   ")
    print("="*60)
    print("\nChoose an interface option:")
    print("1. Graphical User Interface (GUI) - Green Theme")
    print("2. Terminal Interface")
    print("3. Exit")
    return input("\nEnter your choice (1-3): ")

def main():
    """Main launcher function"""
    while True:
        choice = show_welcome()
        
        if choice == '1':
            print("\nLaunching GUI interface with Green Theme...")
            try:
                import app_gui
                app_gui.main()
                break
            except ImportError as e:
                print(f"\nError: {str(e)}")
                print("Make sure PyQt6 is installed. Run: pip install PyQt6")
                input("\nPress Enter to continue...")
        
        elif choice == '2':
            print("\nLaunching terminal interface...")
            try:
                import main
                main.main()
                break
            except ImportError as e:
                print(f"\nError: {str(e)}")
                print("Make sure all dependencies are installed. Run: pip install -r requirements.txt")
                input("\nPress Enter to continue...")
        
        elif choice == '3':
            print("\nExiting application. Goodbye!")
            break
        
        else:
            print("\nInvalid choice. Please enter 1, 2, or 3.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 