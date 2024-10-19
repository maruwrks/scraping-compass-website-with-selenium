import mysql.connector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time
import streamlit as st
from tabulate import tabulate as my_tabulate
from firebase_admin import credentials, auth,initialize_app
import pandas as pd
import plotly.express as px

class SepatuSorter:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()

    def sort_harga_termurah(self):

        try:
            self.cursor.execute("""
                                    SELECT nama_sepatu.nomor, nama_sepatu.nama_sepatu, harga.harga, terjual.terjual, rating_sepatu.rating
                                    FROM nama_sepatu
                                    JOIN harga ON nama_sepatu.nomor = harga.nomor
                                    JOIN terjual ON nama_sepatu.nomor = terjual.nomor
                                    JOIN rating_sepatu ON nama_sepatu.nomor = rating_sepatu.nomor
                                    ORDER BY harga ASC
                                """)
            data = self.cursor.fetchall()
            return data
        finally:
            pass

    def sort_harga_termahal(self):
                            
        try:
            self.cursor.execute("""
                                SELECT nama_sepatu.nomor, nama_sepatu.nama_sepatu, harga.harga, terjual.terjual, rating_sepatu.rating
                                FROM nama_sepatu
                                JOIN harga ON nama_sepatu.nomor = harga.nomor
                                JOIN terjual ON nama_sepatu.nomor = terjual.nomor
                                JOIN rating_sepatu ON nama_sepatu.nomor = rating_sepatu.nomor
                                ORDER BY harga DESC
                                """)
            data = self.cursor.fetchall()
            return data
        finally:
            pass

class sepatu:
    def __init__(self):
        self.url = 'https://sepatucompass.com/shop'

        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

        self.browser = webdriver.Chrome(options=chrome_options)
        self.browser.get(self.url)

        time.sleep(5)

        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ssss",
        )
        self.wait = WebDriverWait(self.browser, 10)
        self.shopping_cart = []
        self.cursor = self.connection.cursor()
        self.scraping_done = False

        self.scraping_done = st.session_state.get('scraping_done', False)

        existing_data = self.scrape_data()

        if not existing_data[0] or not existing_data[1]:
            self.save_database(existing_data[0], existing_data[1])


    def scrape_data(self):
        try:
            if self.scraping_done:
                print("Data has already been scraped. Skipping...")
                return [], []

            self.cursor.execute("SELECT COUNT(*) FROM nama_sepatu")
            count = self.cursor.fetchone()[0]

            if count > 0:
                self.cursor.execute("SELECT nama_sepatu FROM nama_sepatu")
                nama = self.cursor.fetchall()

                self.cursor.execute("SELECT harga FROM harga")
                harga = self.cursor.fetchall()

                return nama, harga

        except Exception as e:
            print(f"Error in scrape_data: {str(e)}")

        data = self.scrape_nama(), self.scrape_harga()
        self.save_database(data[0], data[1])

        self.scraping_done = True
        st.session_state.scraping_done = True

        return data

    def close_connection(self):
        try:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()

        except Exception as e:
            print(f"Error closing connection: {str(e)}")

    def scrape_nama(self):
        data=[]
        try:
            data_table = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@class="col-6 col-lg-4"]'))
                )

            for i in data_table:
                nama_parameter = i.find_element(By.CLASS_NAME, 'card-title')
                nama = nama_parameter.text.strip() if nama_parameter else "N/A"

                if nama != 'N/A':
                    data.append((nama,))

        except Exception as e:
            print(f"Error di scrape nama: {str(e)}")

        return data

    def scrape_harga(self):

        try:
            data_table = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@class="col-6 col-lg-4"]'))
            )

            data = []

            for i in data_table:
                harga_parameter = i.find_element(By.CLASS_NAME, 'card-text')
                harga = harga_parameter.text.strip() if harga_parameter else "N/A"

                if harga != 'N/A':
                    if harga and any(c.isdigit() for c in harga):
                        harga_numeric = int(''.join(filter(str.isdigit, harga)))
                    else:
                        harga_numeric = 0

                    data.append((harga_numeric,))

        except Exception as e:
            print(f"Error di scrape harga: {str(e)}")
        return data

    def save_database(self, nama, harga):
        cursor = self.connection.cursor()

        try:
            cursor.execute('''CREATE TABLE IF NOT EXISTS nama_sepatu(
                                nomor INT AUTO_INCREMENT PRIMARY KEY,
                                nama_sepatu VARCHAR(255) NOT NULL)''')
                
            cursor.execute('''CREATE TABLE IF NOT EXISTS harga(
                                nomor INT AUTO_INCREMENT PRIMARY KEY,
                                harga INT NOT NULL)''')

            nama_values = [name[0] for name in nama]

            if harga is not None:
                harga_values = [price[0] for price in harga]

                for name in nama_values:
                    cursor.execute("SELECT * FROM nama_sepatu WHERE nama_sepatu = %s", (name,))
                    existing_data = cursor.fetchall()

                    if not existing_data:
                        cursor.execute('INSERT INTO nama_sepatu (nama_sepatu) VALUES (%s)', (name,))
                
                for price in harga_values:
                    cursor.execute("SELECT * FROM harga WHERE harga = %s", (price,))
                    existing_data = cursor.fetchall()

                    if not existing_data:
                        cursor.execute('INSERT INTO harga (harga) VALUES (%s)', (price,))

                self.connection.commit()

                print("Data inserted into the database.")

        finally:
            cursor.close()  

    def close_browser(self):
        if self.browser:
            self.browser.quit()

    def get_product_details(self, product_name):
        try:
            self.cursor.execute("""
                SELECT nama_sepatu.nomor, nama_sepatu.nama_sepatu, harga.harga, terjual.terjual, rating_sepatu.rating
                FROM nama_sepatu
                JOIN harga ON nama_sepatu.nomor = harga.nomor
                JOIN terjual ON nama_sepatu.nomor = terjual.nomor
                JOIN rating_sepatu ON nama_sepatu.nomor = rating_sepatu.nomor
                WHERE nama_sepatu.nama_sepatu = %s
            """, (product_name,))

            product_data = self.cursor.fetchone()

            if not product_data:
                st.error(f"Product not found: {product_name}")
                return None

            return product_data

        except Exception as e:
            st.error(f"Error in get_product_details: {str(e)}")
            return None
    
    def terjual(self):
        
        try:
            cursor = self.connection.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS terjual(
                                nomor INT AUTO_INCREMENT PRIMARY KEY,
                                terjual INT NOT NULL)''')
            
            jual = [
                (305), (94), (510), (291),
                (50), (87), (3), (1),
                (4), (6), (220), (550),
                (436), (560), (38), (15),
                (36), (30)
            ]
            for i in jual:
                cursor.execute("SELECT * FROM terjual WHERE terjual = %s", (i,))
                existing_data = cursor.fetchall()
                if not existing_data:
                    cursor.executemany('INSERT INTO terjual (terjual) VALUES (%s)', [(item,) for item in jual])

            self.connection.commit()
        except Exception as e:
            print(f'Error in database jual {e}')
        finally:
            cursor.close()

    def rating(self):
        try:
            cursor = self.connection.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS rating_sepatu(
                                nomor INT AUTO_INCREMENT PRIMARY KEY,
                                rating FLOAT NOT NULL)''')
            
            self.connection.commit()

            rating = [
                4.9, 5.0, 4.9, 4.9,
                4.8, 4.9, 5.0, 5.0,
                5.0, 5.0, 4.8, 4.7,
                4.9, 4.8, 5.0, 4.8,
                4.8, 4.6
            ]

            for i in rating:
                cursor.execute("SELECT * FROM rating_sepatu WHERE rating = %s", (i,))
                existing_data = cursor.fetchall()

                if not existing_data:
                    cursor.executemany('INSERT INTO rating_sepatu (rating) VALUES (%s)', [(item,) for item in rating])

            self.connection.commit()

        except Exception as e:
            print(f'Error in database jual {e}')
        finally:
            cursor.close()

    def tampil(self):
        try:
            if self.cursor:
                self.cursor = self.connection.cursor()
                self.cursor.execute("""
                    SELECT nama_sepatu.nama_sepatu, harga.harga, terjual.terjual, rating_sepatu.rating
                    FROM nama_sepatu
                    JOIN harga ON nama_sepatu.nomor = harga.nomor
                    JOIN terjual ON nama_sepatu.nomor = terjual.nomor
                    JOIN rating_sepatu ON nama_sepatu.nomor = rating_sepatu.nomor
                """)
                data = self.cursor.fetchall()

                if not data:
                    print("No data available.")
                    return

                header = ["Nama Sepatu", "Harga", "Terjual", "Rating"]

                data_for_table = [(item[0], item[1], item[2], item[3]) for item in data]

                print(my_tabulate(data_for_table, headers=header, tablefmt="pretty"))

            else:
                print("Cursor is not initialized.")

        except Exception as e:
            print(f"Error in tampil: {str(e)}")

        finally:
            self.close_connection()
    
    def add_item(self, nama, harga):
        cursor = self.connection.cursor()

        try:
            cursor.execute('''CREATE TABLE IF NOT EXISTS nama_sepatu(
                                nomor INT AUTO_INCREMENT PRIMARY KEY,
                                nama_sepatu VARCHAR(255) NOT NULL)''')
                
            cursor.execute('''CREATE TABLE IF NOT EXISTS harga(
                                nomor INT AUTO_INCREMENT PRIMARY KEY,
                                harga INT NOT NULL)''')

            cursor.execute("INSERT INTO nama_sepatu (nama_sepatu) VALUES (%s)", (nama,))
            cursor.execute("INSERT INTO harga (harga) VALUES (%s)", (harga,))

            self.connection.commit()

            print(f"Item {nama} added to the database.")

        finally:
            cursor.close()

class Authentication:
    def __init__(self):
        self.firebase_initialized = False

    def initialize_firebase(self):
        if not self.firebase_initialized:
            try:
                cred = credentials.Certificate('login-register-firebase-381e2-ef003927bf5d.json')
                initialize_app(cred)
                self.firebase_initialized = True
            except ValueError as e:
                if "The default Firebase app already exists" not in str(e):
                    raise

    def login(self, email, password):
        self.initialize_firebase()
        try:
            user = auth.get_user_by_email(email)
            return True, user
        except Exception as e:
            return False, str(e)

class Sepatu(sepatu):
    def __init__(self):
        super().__init__()

    def calculate_total_price(self, items):
        total_price = sum(item[0] for item in items)
        return total_price

    def buyer_input(self):
        try:
            nama, harga = self.scrape_data()

            selected_products = st.multiselect("Select the products you want to buy:", self.get_product_names())
            color = st.text_input("Enter the color (cream/blue/black/red):")
            size = st.number_input("Enter the size (35,36,37,38,39,40,41,42,43,44,45,46):", step=1)
            alamat = st.text_input("Masukkan alamat: ")

            total_price = 0
            data = []
            for product_name in selected_products:
                nomor, nama_sepatu, harga, terjual, rating = self.get_product_details(product_name)

                if nomor is not None and nama_sepatu is not None and harga is not None and terjual is not None and rating is not None:
                    current_total_price = self.calculate_total_price([(harga, terjual)])
                    total_price += current_total_price

                    st.write(f"\nProduct Details:\nName: {nama_sepatu}\nPrice: {harga}\nTerjual: {terjual}\nRating: {rating}\n")
                    st.write(f"Color: {color}\nSize: {size}\nCurrent Product Price: {harga}")
                    data.append((nomor, nama_sepatu, harga, color, size, alamat, current_total_price))
                else:
                    st.error(f"Error retrieving product details for: {product_name}")

            total_price = sum(item[-1] for item in data)

            st.write(f"\nTotal Price for Selected Products: {total_price}")

            if st.button("Beli"):
                self.save_to_excel(data, size, color, alamat, total_price)

            custom_header = ["ID", "Product Name", "Price", "Color", "Size", "Address", "Total Price"]
            st.write("### Table Data:")
            st.write(pd.DataFrame(data, columns=custom_header))


            return selected_products, color, size, alamat
        except ValueError as ve:
            st.error(f"Error in buyer_input: {str(ve)}")
            return None

    def get_product_names(self):
        try:
            self.cursor.execute("SELECT nama_sepatu FROM nama_sepatu")
            products = self.cursor.fetchall()
            return [product[0] for product in products]
        
        except Exception as e:
            st.error(f"Error fetching product names: {str(e)}")
            return []

    def buy_sepatu(self):
        try:
            selected_products, color, size, alamat = self.buyer_input()

            if not selected_products or color is None or size is None or alamat is None:
                return

            data = []
            total_price = 0
            for product_name in selected_products:
                nomor, nama_sepatu, harga, terjual, rating = self.get_product_details(product_name)

                if nomor is not None and nama_sepatu is not None and harga is not None and terjual is not None and rating is not None:
                    current_total_price = self.calculate_total_price([(harga, terjual)])
                    total_price += current_total_price 


                    st.write(f"\nProduct Details:\nName: {nama_sepatu}\nPrice: {harga}\nTerjual: {terjual}%\nRating: {rating}\n")
                    st.write(f"Color: {color}\nSize: {size}\nCurrent Product Price: {current_total_price}")
                    data.append((nomor, nama_sepatu, harga, terjual, rating, color, size, alamat, current_total_price))
                else:
                    st.error(f"Error retrieving product details for: {product_name}")

            total_price = self.calculate_total_price([(harga, terjual) for _, _, harga, terjual, _, _, _, _, current_total_price in data])

            st.subheader(f"\nTotal harga : {total_price}")

            if st.button("Beli"):
                self.save_to_excel(data, size, color, alamat,total_price)

            custom_header = ["ID", "Product Name", "Price", "Sold", "Rating", "Color", "Size", "Address", "Price"]
            st.write("### Table Data:")
            st.write(pd.DataFrame(data, columns=custom_header))

            return selected_products, color, size, alamat
        except ValueError:
            st.error("Invalid input. Please enter a valid size.")
            return None

    def save_to_excel(self, data, size, color, alamat, total_price):
        try:
            try:
                df = pd.read_excel("sepatu_data.xlsx")
            except FileNotFoundError:
                df = pd.DataFrame(columns=["Nomor", "Nama Sepatu", "Harga", "Color", "Size", "Alamat", "Total Price"])

            for item in data:
                nomor, nama_sepatu, harga, color, size, alamat, total_price = item

                new_data = pd.DataFrame({
                    "Nomor": [nomor],
                    "Nama Sepatu": [nama_sepatu],
                    "Harga": [harga],
                    "Color": [color],
                    "Size": [size],
                    "Alamat": [alamat],
                    "Total Price": [total_price]
                })

                df = pd.concat([df, new_data], ignore_index=True)

            df.to_excel("sepatu_data.xlsx", index=False)
 
            st.success("Data sedang diproses silahkan tunggu pesanan sampai")

        except Exception as e:
            print(f"Error saving to Excel: {str(e)}")

class App:
    def main(self):
        st.title("Aplikasi Sepatu")

        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False

        role = st.selectbox("Pilih Sebagai:", ["Buyer", "Seller"])
        masuk = st.selectbox("Login/Register:", ["Login", "Register"])

        if role == "Buyer":
            if masuk == "Login":
                st.header("Login Buyer")
                email = st.text_input("Email:")
                password = st.text_input("Password:", type="password")

                if st.button("Login") or st.session_state.logged_in:
                    st.session_state.logged_in = True
                    auth_instance = Authentication()
                    login_success, user = auth_instance.login(email, password)
                    if login_success:
                        print("Berhasil login")
                        st.success("Login berhasil!")

                        if st.checkbox("Tampilkan Grafik Harga dan Rating"):
                            try:
                                connection = mysql.connector.connect(
                                    host="localhost",
                                    user="root",
                                    password="",
                                    database="data_sepatu",
                                )

                                df_harga = pd.read_sql_query("""
                                    SELECT nama_sepatu, harga
                                    FROM nama_sepatu
                                    JOIN harga ON nama_sepatu.nomor = harga.nomor
                                    ORDER BY harga DESC
                                """, connection)

                                fig_harga = px.bar(df_harga, x='nama_sepatu', y='harga', color='nama_sepatu',
                                                  labels={'nama_sepatu': 'Sepatu', 'harga': 'Harga'},
                                                  title='Grafik Harga Sepatu (Tertinggi ke Terendah)')

                                st.plotly_chart(fig_harga)

                                df_rating = pd.read_sql_query("""
                                    SELECT nama_sepatu, rating
                                    FROM nama_sepatu
                                    JOIN rating_sepatu ON nama_sepatu.nomor = rating_sepatu.nomor
                                    ORDER BY rating DESC
                                """, connection)

                                fig_rating = px.scatter(df_rating, x='nama_sepatu', y='rating', color='nama_sepatu',
                                                    labels={'nama_sepatu': 'Sepatu', 'rating': 'Rating'},
                                                    title='Grafik Rating Sepatu (Tertinggi ke Terendah)')

                                st.plotly_chart(fig_rating)

                                st.success("Grafik berhasil ditampilkan.")

                                st.stop()

                            except Exception as e:
                                st.error(f"Error fetching data from MySQL: {str(e)}")
                            finally:
                                if connection.is_connected():
                                    connection.close()

                        sepatu_instance = Sepatu()
                        sepatu_instance.buyer_input()

                    else:
                        st.error(f"Login gagal: {user}")

            elif masuk == "Register":
                st.header("Daftar akun")
                email = st.text_input("Email:")
                password = st.text_input("Password:", type="password")
                confirm_password = st.text_input("Confirm Password:", type="password")

                if st.button("Buat Akun"):
                    if password == confirm_password:
                        success, user = Authentication.register(email, password)
                        if success:
                            st.success("Akun berhasil dibuat")
                        else:
                            st.error(f"Gagal membuat akun: {user}")
                    else:
                        st.error("Password dan konfirmasi password tidak sesuai.")

        elif role == "Seller":
            if masuk == "Login":
                st.header("Login Seller")
                email = st.text_input("Email:")
                password = st.text_input("Password:", type="password")

                if st.button("Login") or st.session_state.logged_in:
                    st.session_state.logged_in = True
                    auth_instance = Authentication()
                    login_success, user = auth_instance.login(email, password)

                    if login_success:
                        print("Berhasil login")
                        st.success("Login berhasil!")

                        if st.session_state.logged_in:
                            st.header("Data Pembeli")

                            df_buyer_data = pd.read_excel("sepatu_data.xlsx")
                            st.table(df_buyer_data)

                            st.header("Tambah Produk")
                            nama_sepatu = st.text_input("Nama Sepatu: ")
                            harga = st.number_input("Harga: ")
                            warna = st.text_input("Warna: ")
                            ukuran = st.text_input("Ukuran: ")

                            if st.button("Tambah Produk"):
                                sepatu_instance = Sepatu()
                                sepatu_instance.add_item(nama_sepatu, harga)
                                sepatu_instance.save_database([(nama_sepatu,)], [(harga,)])

                                st.success(f"Produk {nama_sepatu} berhasil ditambahkan!")

                            connection = mysql.connector.connect(
                                host="localhost",
                                user="root",
                                password="",
                                database="data_sepatu",
                            )
                            if connection.is_connected():
                                connection.close()

                    else:
                        st.error(f"Login gagal: {user}")

if __name__ == "__main__":
    sepatu_instance = sepatu()
    sepatu_instance.rating()
    app_instance = App()
    app_instance.main()
    sepatu_instance.close_browser()