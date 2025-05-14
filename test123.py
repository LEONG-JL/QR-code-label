from flask import Flask, render_template
import pandas as pd
import qrcode
import os
import pathlib
import traceback

app = Flask(__name__)

EXCEL_PATH = r"C:\Users\TAS Xavier\Downloads\RESMED_DATABASE_060525.xlsx"
QR_DIR = './static/qr'

def parse_udi(udi):
    try:
        parts = {}
        udi = udi.replace('(', '').replace(')', '')

        i = 0
        while i < len(udi):
            ai = udi[i:i+2]
            i += 2
            if ai == '00':
                parts['gtin'] = udi[i:i+14]
                i += 14
            elif ai == '17':  # Expiry date (not used)
                i += 6
            elif ai == '10':  # LOT
                lot = ''
                while i < len(udi) and not udi[i:i+2].isdigit():
                    lot += udi[i]
                    i += 1
                parts['lot'] = lot
            elif ai == '21':  # Serial Number
                sn = ''
                while i < len(udi):
                    sn += udi[i]
                    i += 1
                parts['sn'] = sn
            else:
                i += 1
        return parts
    except Exception as e:
        raise ValueError(f"Failed to parse UDI: {e}")

def generate_qr_code(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(filename)
    return filename

@app.route('/')
def process_label():
    try:
        # Simulated scanned UDI (replace with actual scanned input later)
        scanned_udi = "(00)01234567890123(10)LOT123(21)SN789"

        udi_parts = parse_udi(scanned_udi)
        gtin = udi_parts.get('gtin')
        lot = udi_parts.get('lot', '')
        sn = udi_parts.get('sn', '')

        # Load the Excel database
        df = pd.read_excel(EXCEL_PATH)
        row = df[df['RESMED GTIN'] == gtin]

        if row.empty:
            return render_template('lmterror.html', error_message=f"GTIN '{gtin}' not found in Excel database.")

        row = row.iloc[0]
        sku = str(row['RESMED SKU'])
        description = row['RESMED DESCRIPTION']
        tracking_code = row['ITEM TRACKING CODE'].strip().upper()

        # Determine whether to use LOT or SN
        if tracking_code == 'LOT':
            identifier = lot
        elif tracking_code == 'SN':
            identifier = sn
        else:
            return render_template('lmterror.html', error_message=f"Invalid tracking code '{tracking_code}' for SKU {sku}")

        # Generate QR codes
        qr_sku_path = generate_qr_code(sku, f"{QR_DIR}/sku_{sku}.png")
        qr_id_path = generate_qr_code(identifier, f"{QR_DIR}/id_{identifier}.png")

        return render_template('lmtresults.html',
                               product_name=description,
                               product_sku=sku,
                               identifier=identifier,
                               udi=scanned_udi,
                               qr_sku=qr_sku_path,
                               qr_id=qr_id_path)

    except Exception as e:
        return render_template('lmterror.html', error_message=traceback.format_exc())

if __name__ == '__main__':
    app.run(debug=True)
