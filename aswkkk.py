import requests
from bs4 import BeautifulSoup
import tkinter as tk
import sqlite3
from forex_python.converter import CurrencyRates

# Function to create database table
def create_table():
    conn = sqlite3.connect('product_prices.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  ebay_price TEXT,
                  flipkart_title TEXT,
                  flipkart_price TEXT)''')
    conn.commit()
    conn.close()

# Function to insert data into the database
def insert_data(product_name, ebay_price, flipkart_title, flipkart_price):
    conn = sqlite3.connect('product_prices.db')
    c = conn.cursor()
    c.execute("INSERT INTO products (name, ebay_price, flipkart_title, flipkart_price) VALUES (?, ?, ?, ?)",
              (product_name, ebay_price, flipkart_title, flipkart_price))
    conn.commit()
    conn.close()

# Function to retrieve data from the database
def retrieve_data():
    conn = sqlite3.connect('product_prices.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    data = c.fetchall()
    conn.close()
    return data

def get_ebay_product_info(product_name, currency="USD"):
    ebay_url = f"https://www.ebay.in/sch/i.html?_nkw={product_name.replace(' ', '+')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(ebay_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        price_elements = soup.find_all('span', {'class': 's-item__price'})
        if len(price_elements) > 1:
            second_price_text = price_elements[1].text.strip()
            if second_price_text.startswith('$') or second_price_text.startswith('₹'):
                if currency != "USD":
                    c = CurrencyRates()
                    exchange_rate = c.get_rate("USD", currency)
                    second_price_text = f"{float(second_price_text[1:].replace(',', '')) * exchange_rate:.2f} {currency}"
                return second_price_text
        else:
            return "Product price not found."
    return None

def get_flipkart_product_info(product_name, currency="USD"):
    flipkart_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '%20')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(flipkart_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        product_elements = soup.find_all('div', {'class': '_4rR01T'})
        if product_elements:
            first_product = product_elements[0]
            title = first_product.text.strip()
            price_element = first_product.find_next('div', {'class': '_30jeq3'})
            if price_element:
                price = price_element.text.strip()
                if currency != "INR":
                    c = CurrencyRates()
                    exchange_rate = c.get_rate("INR", currency)
                    price = f"{float(price[1:].replace(',', '')) * exchange_rate:.2f} {currency}"
                return title, price
        else:
            return "Product not found on Flipkart."
    return None, None

def compare_prices(product_names, currency="USD"):
    results = []
    for product_name in product_names:
        ebay_price = get_ebay_product_info(product_name, currency)
        flipkart_title, flipkart_price = get_flipkart_product_info(product_name, currency)

        insert_data(product_name, ebay_price, flipkart_title, flipkart_price)

        ebay_info = f"\n\neBay\nTitle: {product_name}\nPrice: {ebay_price}" if ebay_price else f"\n\nUnable to retrieve information from eBay for {product_name}."
        flipkart_info = f"\n\nFlipkart\nTitle: {flipkart_title}\nPrice: {flipkart_price}" if flipkart_price else f"\n\nUnable to retrieve price information from Flipkart for {product_name}."

        results.append(ebay_info + flipkart_info)

    result_label.config(text='\n'.join(results))

def show_database():
    data = retrieve_data()
    if data:
        database_text = "\n".join([f"ID: {row[0]}, Name: {row[1]}, eBay Price: {row[2]}, Flipkart Title: {row[3]}, Flipkart Price: {row[4]}" for row in data])
        database_label.config(text=database_text)
    else:
        database_label.config(text="Database is empty.")

def on_submit():
    product_names = entry.get().split(",")
    compare_prices([name.strip() for name in product_names], currency_dropdown.get())

# GUI setup
root = tk.Tk()
root.title("Price Comparison GUI")
frame = tk.Frame(root)
frame.pack(padx=20, pady=20)

heading_label = tk.Label(frame, text="Price Comparison GUI", font=("Times New Roman", 22, "bold"),bg="lightblue")
heading_label.grid(row=0, columnspan=2, padx=5, pady=5)

# Set background color using configure method
result_label = tk.Label(frame, text="", bg="lightyellow")
result_label.grid(row=5, columnspan=2, pady=10)

label = tk.Label(frame, text="Enter the names of the products (separated by commas):")
label.grid(row=1, columnspan=2, padx=5, pady=5)

entry = tk.Entry(frame, width=40)
entry.grid(row=2, columnspan=2, padx=5, pady=5)

currency_label = tk.Label(frame, text="Select Currency:")
currency_label.grid(row=3, column=0, padx=5, pady=5)

currency_options = ["USD", "EUR", "GBP", "INR"]  # Add more currencies as needed
currency_dropdown = tk.StringVar()
currency_dropdown.set("USD")
currency_menu = tk.OptionMenu(frame, currency_dropdown, *currency_options)
currency_menu.grid(row=3, column=1, padx=5, pady=5)

submit_button = tk.Button(frame, text="Compare Prices", command=on_submit)
submit_button.grid(row=4, columnspan=2, pady=10)

result_label = tk.Label(frame, text="")
result_label.grid(row=5, columnspan=2, pady=10)

database_button = tk.Button(frame, text="Show Database", command=show_database)
database_button.grid(row=6, columnspan=2, pady=10)

database_label = tk.Label(frame, text="")
database_label.grid(row=7, columnspan=2, pady=10)

# Create database table
create_table()

root.mainloop()
