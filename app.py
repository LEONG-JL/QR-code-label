from flask import Flask, render_template, request, jsonify
from pathlib import Path
import qrcode
import pandas as pd
import os
import traceback
import pathlib
import imgkit
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from brother_ql.conversion import convert

app = Flask(__name__)

# Paths
BASE_DIR = pathlib.Path(__file__).parent.resolve()
EXCEL_DB_PATH = os.path.join(BASE_DIR, 'RESMED_DATABASE_060525.xlsx')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
SKU_DIR = os.path.join(STATIC_DIR, 'sku')
SERIAL_DIR = os.path.join(STATIC_DIR, 'serialno')
LABEL_DIR = os.path.join(STATIC_DIR, 'label')

# Ensure directories exist
os.makedirs(SKU_DIR, exist_ok=True)
os.makedirs(SERIAL_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product-info/', methods=['POST'])
def product_info():
    try:
        data = request.get_json()
        barcode = data.get('barcode', '').strip()
        UDI_trimmed = barcode[4:]
        gtin_from_udi = int(UDI_trimmed[:12])

        # Load Excel database
        df = pd.read_excel(EXCEL_DB_PATH)
        df['RESMED GTIN'] = pd.to_numeric(df['RESMED GTIN'], errors='coerce')
        df.dropna(subset=['RESMED GTIN'], inplace=True)
        df['RESMED GTIN'] = df['RESMED GTIN'].astype(int)
        row = df[df['RESMED GTIN'] == gtin_from_udi]

        if row.empty:
            return jsonify({"error": f"GTIN {gtin_from_udi} not found in the database."}), 404

        product_name = row.iloc[0]['RESMED DESCRIPTION']
        product_sku = str(row.iloc[0]['RESMED SKU'])

        return jsonify({
            "product_name": product_name,
            "product_sku": product_sku
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/lmtpreview/', methods=['POST'])
def lmtpreview():
    try:
        barcode = request.form['barcode']
        UDI_trimmed = barcode[4:]
        gtin_from_udi = int(UDI_trimmed[:12])

        df = pd.read_excel(EXCEL_DB_PATH)
        df['RESMED GTIN'] = pd.to_numeric(df['RESMED GTIN'], errors='coerce')
        df.dropna(subset=['RESMED GTIN'], inplace=True)
        df['RESMED GTIN'] = df['RESMED GTIN'].astype(int)
        row = df[df['RESMED GTIN'] == gtin_from_udi]

        if row.empty:
            raise ValueError(f"GTIN {gtin_from_udi} not found in the database.")

        product_name = row.iloc[0]['RESMED DESCRIPTION']
        product_sku = str(row.iloc[0]['RESMED SKU'])

        return jsonify({
            "product_name": product_name,
            "product_sku": product_sku,
            "sku_url": url_for('static', filename=f'sku/{product_sku}.png'),
            "serialno_url": url_for('static', filename=f'serialno/{product_sku}.png')
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
