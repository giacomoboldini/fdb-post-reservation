
import json
import os
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request, AuthorizedSession
from tkinter import messagebox
import requests
import pygsheets
import pandas as pd
from fpdf import FPDF


def google_login(creds_file='google_secrets.json',
                 token_file='sheets.googleapis.com-python.json'):
    """
    Try a login to Google services using an already saved token. If the
    token is expired, the user will be asked to login again and the new
    token will be saved.

    Args:
        creds_file (str): The path to the client secrets file.
        token_file (str): The path to the token file.

    Returns:
        Credentials: The authenticated credentials.
    """
    # Authorization for both Google Sheets and Google Drive (like pygsheets).
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']

    # Check if the user is already logged in.
    google_login, _ = check_google_login(token_file)
    if google_login:
        login_again = messagebox.askyesno("Google Login", "Do you want to login to Google again?")
        if not login_again:
            return None

    creds = None

    message = "You are going to be prompted in the browser.\nFollow the instructions and authorize the app."
    messagebox.showinfo("OAuth Login", message)

    # If there are no valid credentials, prompt the user to log in.
    # Add instructions to the message box not in the terminal.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file,
                                                             SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return creds


def check_google_login(token_file='sheets.googleapis.com-python.json') -> (bool, str):
    """
    Check if the user is already logged in to Google services.

    Args:
        token_file (str): The path to the token file.

    Returns:
        tuple: (bool, str) True and account if the login is successful. False
        and error message otherwise.
    """
    print("Checking Google login... " + token_file)
    if not os.path.exists(token_file):
        print("Token file not found.")
        return False, "Token file not found."

    try:
        creds = Credentials.from_authorized_user_file(token_file)
        print("Credentials loaded:", creds)

        if creds and creds.valid:
            print("Credentials are valid.")
            return True, creds.account
        else:
            print("Credentials are invalid.")
            return False, "Login failed: Invalid credentials."
    except Exception as e:
        print("Error loading credentials:", str(e))
        return False, f"Login failed: {str(e)}"


def check_whatsapp_login(token_file='whatsapp_secrets.json', phone_number_key='test'):
    """
    Check if the user is logged in to WhatsApp Business API by requesting the business profile.

    Args:
        secrets_file (str): The path to the secrets file.

    Returns:
        tuple: (bool, str) True if the login is successful, and an error message otherwise.
    """
    try:
        # Load the secrets
        with open(token_file, 'r') as f:
            secrets = json.load(f)

        access_token = secrets.get('access_token')
        phone_number_id = secrets.get('phone_number_id')[phone_number_key]

        if not access_token or not phone_number_id:
            return False, "Missing access token or phone number ID in secrets file."

        url = f'https://graph.facebook.com/v20.0/{phone_number_id}/whatsapp_business_profile?fields=about,address,description,email,profile_picture_url,websites,vertical'

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return True, "Login successful."
            else:
                return False, "Unexpected response format."
        else:
            return False, f"API request failed with status code {response.status_code}: {response.text}"

    except FileNotFoundError:
        return False, "Secrets file not found."
    except json.JSONDecodeError:
        return False, "Error decoding secrets file."
    except Exception as e:
        return False, str(e)


def download_worksheet(file_id: str, sheet_name: str, google_secr: str) -> pd.DataFrame:
    """
    Connect to Google Drive and get the specified worksheet from the Google Sheets
    file as a pandas dataframe. Also filter out unuseful columns and rows with no
    table number.

    Args:
        file_id (str): the ID of the Google Sheets file.
        sheet_name (str): the name of the Google Sheets worksheet.
    Returns:
        pd.DataFrame: The dataframe of the specified worksheet.
    """
    # Connect to Google Drive and get the spreadsheet.
    print(sheet_name)
    client = pygsheets.authorize(google_secr)
    spreadsheet = client.open_by_key(file_id)
    sheet = spreadsheet.worksheet_by_title(sheet_name)

    # Convert the worksheet to a pandas dataframe.
    # TODO: Fix the warning generated by the conversion.
    df_dump = sheet.get_as_df(include_tailing_empty=False)

    # Maintain only useful columns.
    cols = ["Nome", "Telefono", "Num persone", "Num tavoli", "Tavolo/i"]
    not_manadatory_cols = ["Num spiedi"]

    df = df_dump[cols]
    try:
        df_not_mandatory = df_dump[not_manadatory_cols]
        # Join df and df_not_mandatory
        df = df.join(df_not_mandatory)
    except KeyError as e:
        print(f"Column {e} not found in the dataframe. Continuing.")

    # Replace empty strings with pd.NA.
    df.replace("", pd.NA, inplace=True)
    # Drop rows with no 'Num tavoli' value.
    df = df[df["Num tavoli"].notna()]

    return df


def extract_number_and_letter(value):
    match = re.match(r"(\d+)([A-Z])", value)
    if match:
        number, letter = match.groups()
        return int(number), letter
    return 0, ''  # Default return if the pattern does not match


def generate_table_labels_pdf(
        df: pd.DataFrame, filename: str, output_dir: str) -> None:
    """
    Generate a PDF containing pages with labels to attach to booked tables.

    Precondition:
    This function relies on the "Nome" and "Num tavoli" columns of the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing booking information.
        filename (str): Name of the output PDF file (without extension).
        output_dir (str): Output directory path.
        booked_table_ids (list): List of booked table IDs.
    """

    df = df.dropna(subset=["Tavolo/i"])
    df = df[df["Tavolo/i"].str.strip() != ""]

    # Extract the first table ID from "Tavolo/i" column and add separate columns for sorting
    df['first_table_id'] = df['Tavolo/i'].apply(lambda x: x.split(";")[0])
    df['numeric_part'] = df['first_table_id'].apply(lambda x: extract_number_and_letter(x)[0])
    df['letter_part'] = df['first_table_id'].apply(lambda x: extract_number_and_letter(x)[1])
    # Sort DataFrame by the numeric and letter parts of the first table ID
    df = df.sort_values(by=['numeric_part', 'letter_part'])

    pdf = FPDF(orientation="L", format="A4")

    for _, row in df.iterrows():

        pdf.add_page()

        # Prenotato label with smaller font size
        pdf.set_font('Arial', 'B', 60)
        pdf.cell(w=0, h=40, txt='PRENOTATO', align="C", ln=2)

        name = row['Nome'].upper()
        tables_num = int(row["Num tavoli"])
        print(f"Printing page for {name} with {tables_num} tables...")

        # Adjust font size for the name based on its length
        name_font_size = 100
        max_name_length = 10  # Define the maximum length for the name to fit in one line
        if len(name) > max_name_length:
            name_font_size = max(30, 100 - (len(name) - max_name_length) * 5)

        pdf.set_font('Arial', 'B', name_font_size)
        pdf.cell(w=0, h=70, align="C", txt=name, ln=2)

        # Number of tables and table IDs
        try:
            booked_table_ids = row["Tavolo/i"].split(";")
        except AttributeError:
            print(f"Error: Tavolo/i column not found in the row.")
            booked_table_ids = []
        table_ids_text = '-'.join(map(str, booked_table_ids))
        pdf.set_font('Arial', 'B', 50)

        # Number of tables and table IDs combined
        pdf.cell(w=0, h=25, align="C", txt=f"{tables_num} TAVOL{'I' if tables_num > 1 else 'O'}", ln=2)
        pdf.cell(w=0, h=25, align="C", txt=table_ids_text,ln=2)
        pdf.set_font('Arial', 'B', 50)

        # Check if "Num spiedi" column exists
        if "Num spiedi" in df.columns and not pd.isna(row["Num spiedi"]):
                num_spiedi = row["Num spiedi"]
                pdf.set_font('Arial', 'B', 20)
                pdf.cell(w=0, h=10, align="C", txt=f"{num_spiedi} SPIEDI", ln=2)

    # Create the output directory if it doesn't exist.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Output the file.
    pdf_file_path = os.path.join(output_dir, f"{filename}.pdf")
    pdf.output(pdf_file_path, 'F')
    print(f"File {pdf_file_path} written.")

    return


def generate_map_pdf_png(creds, file_id, sheet_id, output_dir, filename) -> None:
    """
    Generate a PDF and a PNG of a specific range from a Google Sheet.

    Args:
        file_id (str): The ID of the Google Sheet file.
        sheet_id (str): The ID of the specific sheet within the Google Sheet file.
        output_dir (str): The directory to save the output files.
        filename (str): The base name of the output files (without extension).

    Raises:
        Exception: If there is an issue downloading the PDF or converting it to PNG.
    """

    range = "t1:y43"
    dwn_url = 'https://docs.google.com/spreadsheets/d/' + file_id \
              + '/export?format=pdf&gid=' + sheet_id \
              + "&range=" + range \
              + "&scale=4&fith=true" \
              + "&horizontal_alignment=CENTER&vertical_alignment=TOP" \
              + "&gridlines=false"

    authed_session = AuthorizedSession(creds)
    if not authed_session:
        raise Exception("Failed to authenticate with Google.")
    response = authed_session.get(dwn_url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to download PDF. Status code: {response.status_code}")

    # Create the output directory if it doesn't exist.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Output the PDF file.
    pdf_file_path = os.path.join(output_dir, f"{filename}.pdf")

    with open(pdf_file_path, "wb") as f:
        f.write(response.content)

    print(f"File {pdf_file_path} written.")

    # Convert PDF to PNG
    # pages = convert_from_path(pdf_file_path, dpi=300)
    # if len(pages) != 1:
    #     raise Exception(
    #         "PDF to PNG conversion resulted in more than one page.")
    # png_file_path = os.path.join(output_dir, f"{filename}.png")
    # pages[0].save(png_file_path, 'PNG')

    # print(f"File {png_file_path} written.")