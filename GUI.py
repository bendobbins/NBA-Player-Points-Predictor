from tkinter import *
import scrape

# Create Tkinter window
window = Tk()
window.title("NBA Player Stats Prediction")
window.geometry("365x350+10+20")


def show_message(player):
    """
    Create and display a message with stats of an NBA player or with an error message if stats cannot be created.
    """
    # Add a white label over the area where the message will be displayed to prevent previous messages from interfering
    Label(window, width=355, height=14).place(x=1, y=40)
    Message(window, text=scrape.make_message(player), width=355, justify=CENTER).place(x=1, y=40)


def main():
    """
    Get the name of an NBA player and display a message.
    """
    playerInput = StringVar()
    Message(window, text="Enter the name of a current NBA player to get a prediction for their stats in their next game.", width=355, justify=CENTER).place(x=1, y=1)
    Label(window, text="NBA Player (Full Name): ").place(x=5, y=280)
    Entry(window, textvariable=playerInput).place(x=160, y=280)
    # When the button is clicked, create a message for whatever is currently in the entry box
    Button(window, text="Search", width=7, height=2, command=lambda:show_message(playerInput.get())).place(x=145, y=310)
    window.mainloop()


if __name__ == "__main__":
    main()