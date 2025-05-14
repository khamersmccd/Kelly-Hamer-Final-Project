"""
Gutenberg Word Frequency Tool
Author: Kelly Hamer
Date: May 5, 2025

Description:
This is a program that lets the user:
- Search a book title in the Project Gutenberg database and store the top 10 words
- Download a book from Project Gutenberg using a URL and store the top 10 words
"""

import tkinter as tk             
import sqlite3                   
import urllib.request            
import re                         
from collections import Counter  
from html.parser import HTMLParser 


#HTML Parser to extract book links from Project Gutenberg search results
class GutenbergSearchParser(HTMLParser):
    """
    HTML parser to extract book links from Project Gutenberg search result page.
    Attributes:
        book_links (list): List of found book links
        in_result (bool): Flag to track if inside a result block
    """
    def __init__(self):
        super().__init__()
        self.book_links = []
        self.in_result = False

    def handle_starttag(self, tag, attrs):
        """
        Handle start tags to find book links.
        Parameters:
            tag (str): The HTML tag name
            attrs (list): List of attribute tuples
        """
        attrs = dict(attrs)
        if tag == 'li' and 'class' in attrs and 'booklink' in attrs['class']:
            self.in_result = True
        if self.in_result and tag == 'a' and 'href' in attrs:
            self.book_links.append(attrs['href'])
            self.in_result = False

            
#set up database so ready to store data that we get
def setup_database():
    """Create the database and tables.
        Tables:
            -Books: stores book titles
            -Words: Stores word frequencies for each book
        Returns: None"""
    con = sqlite3.connect('books.db') # Create or connect to a local database file
    cur = con.cursor()

    # Table to store book titles
    cur.execute("CREATE TABLE IF NOT EXISTS Books (title TEXT PRIMARY KEY)")

    # Table to store top words and their frequency for each book
    cur.execute("CREATE TABLE IF NOT EXISTS Words (book_title TEXT, word TEXT, frequency INTEGER)")
    
    con.commit() # Save changes to the database
    con.close() # Close the database connection


#search for book in database and display outputs 
def search_book(title):
    """
    Look for a book by title in the local database and show the top 10 words.

    Parameters:
        title (str): The book title entered by the user

    Returns:
        None
    """
    con = sqlite3.connect('books.db')
    cur = con.cursor()

    # Search for the 10 most frequent words for this book
    cur.execute("SELECT word, frequency FROM Words WHERE book_title = ? ORDER BY frequency DESC LIMIT 10", (title,))
    results = cur.fetchall()
    con.close() 

    output_box.delete('1.0', tk.END) # Clear previous results from the display box
    
    if results:
        for word, freq in results:
            output_box.insert(tk.END, f"{word}: {freq}\n")
    else:
        fetch_and_process_book(title)# If not found locally, search Project Gutenberg


# Function to fetch and process books from Project Gutenberg when given title
def fetch_and_process_book(title):
    """
    Search Project Gutenberg for the book title, download and process the book, store data locally, and display results.
    Parameters:
        title (str): The book title to search for
    Returns:
        None
    """
    try:
        # Search Project Gutenberg
        query = urllib.parse.quote(title)
        search_url = f"https://www.gutenberg.org/ebooks/search/?query={query}"
        response = urllib.request.urlopen(search_url)
        html = response.read().decode('utf-8')

        # Parse search results to find book links
        parser = GutenbergSearchParser()
        parser.feed(html)

        if not parser.book_links:
            output_box.insert(tk.END, "Book was not found.\n")
            return

        # Construct the URL for the plain text version of the first book found
        book_id = parser.book_links[0].split('/')[-1]
        text_url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"

        # Download the book text
        response = urllib.request.urlopen(text_url)
        text = response.read().decode('utf-8')

        # Extract words and count frequency
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        top_words = Counter(words).most_common(10)

        # Store in database
        con = sqlite3.connect('books.db')
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO Books VALUES (?)", (title,))
        cur.executemany("INSERT INTO Words VALUES (?, ?, ?)", [(title, word, freq) for word, freq in top_words])
        con.commit()
        con.close()

        # Display the top 10 words
        output_box.delete('1.0', tk.END)
        for word, freq in top_words:
            output_box.insert(tk.END, f"{word}: {freq}\n")

    except Exception as e:
        output_box.insert(tk.END, f"Book was not found.\n")


#function to handle inputs
def process_input():
    """
    Handle the inputs from the GUI:
    - If either only title is entered or if title and URL entered: use the search_book funtion using the title 
    - If only URL is entered: download the book, extract top 10 words, store in DB
    Returns: None
    """
    title = title_entry.get().strip() 
    url = url_entry.get().strip() 

    if title:
        search_book(title)# If title is given (even with URL), use search by title only

    elif url:
        try:
            response = urllib.request.urlopen(url)
            text = response.read().decode('utf-8')

            # Extract words (3+ letters) and count frequency
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            top_words = Counter(words).most_common(10)

            con = sqlite3.connect('books.db')
            cur = con.cursor()
            cur.execute("INSERT OR IGNORE INTO Books VALUES (?)", (extracted_title,))
            cur.executemany("INSERT INTO Words VALUES (?, ?, ?)", [(extracted_title, word, freq) for word, freq in top_words])
            con.commit()
            con.close()

            output_box.delete('1.0', tk.END)
            for word, freq in top_words:
                output_box.insert(tk.END, f"{word}: {freq}\n")

        except Exception as e:
            output_box.delete('1.0', tk.END)
            output_box.insert(tk.END, f"Error: {e}\n")

    else:
        # Neither title nor URL provided
        output_box.delete('1.0', tk.END)
        output_box.insert(tk.END, "Please enter a title or URL.\n")

#GUI SETUP
from tkinter import *

# create main window
window = Tk()
window.title("Gutenberg Word Frequency Tool")
window.configure(background="lightblue")

# Book Title label
Label(window, text="Enter a book title to search:", bg="lightblue", fg="black",
      font=("Times New Roman", 16)).grid(row=0, column=0, sticky=W, padx=10, pady=5)

# Book Title entry
title_entry = Entry(window, width=50, bg="white")
title_entry.grid(row=1, column=0, sticky=W, padx=10)

# URL label
Label(window, text="(Optional) Paste Project Gutenberg book URL:", bg="lightblue", fg="black",
      font=("Times New Roman", 16)).grid(row=2, column=0, sticky=W, padx=10, pady=5)

# URL entry
url_entry = Entry(window, width=50, bg="white")
url_entry.grid(row=3, column=0, sticky=W, padx=10)

# Search button
Button(window, text="SEARCH", width=10, command=process_input, bg="navy", fg="black",
       font=("Times New Roman", 14)).grid(row=4, column=0, sticky=W, padx=10, pady=10)

# Output label
Label(window, text="Top 10 Words:", bg="lightblue", fg="black",
      font=("Times New Roman", 16)).grid(row=5, column=0, sticky=W, padx=10)

# Output display box
output_box = Text(window, width=70, height=12, wrap=WORD, background="white")
output_box.grid(row=6, column=0, columnspan=2, sticky=W, padx=10, pady=5)

# Exit instructions
Label(window, text="Close this window to exit.", bg="lightblue", fg="black",
      font=("Times New Roman", 14)).grid(row=7, column=0, sticky=W, padx=10)

# Start the GUI loop
setup_database()
window.mainloop()
