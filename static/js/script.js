// Add manufacturer search functionality and input correlation

document.addEventListener('DOMContentLoaded', () => {
    const manufacturerSelect = document.getElementById('manufacturer');
    const brandInput = document.getElementById('brand');
    const itemNoInput = document.getElementById('item-no');
    const skuInput = document.getElementById('sku');
    const udiInput = document.getElementById('udi');
    const descriptionInput = document.getElementById('description');
    const serialInput = document.getElementById('serial');
    const quantityInput = document.getElementById('quantity');
    const barcodeInput = document.getElementById('udi');

    // Sample manufacturer and brand correlation
    const manufacturerData = {
        'Brand 1': '78924',
        'Brand 2': '65432',
        'Brand 3': '12345'
    };

    // Auto-fill item number based on manufacturer selection
    manufacturerSelect.addEventListener('change', (e) => {
        const selectedManufacturer = e.target.value;
        if (manufacturerData[selectedManufacturer]) {
            itemNoInput.value = manufacturerData[selectedManufacturer];
            skuInput.value = manufacturerData[selectedManufacturer] + '-0';
            brandInput.value = selectedManufacturer;
        } else {
            itemNoInput.value = '';
            skuInput.value = '';
            brandInput.value = '';
        }
    });

    // Simple search function for manufacturer dropdown
    const searchManufacturers = (query) => {
        const options = Array.from(manufacturerSelect.options);
        const matchingOption = options.find(option => option.text.toLowerCase().startsWith(query.toLowerCase()));
        if (matchingOption) {
            manufacturerSelect.value = matchingOption.value;
            manufacturerSelect.dispatchEvent(new Event('change'));
        }
    };

    brandInput.addEventListener('input', (e) => {
        searchManufacturers(e.target.value);
    });

    // Auto-populate fields when UDI is scanned
    barcodeInput.addEventListener('input', () => {
        const barcode = barcodeInput.value.trim();
        if (barcode.length > 10) {
            fetch("/lmtpreview/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ barcode: barcode })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                    alert("Error: " + data.error);
                } else {
                    manufacturerSelect.value = "Brand 1";
                    brandInput.value = data.product_name;
                    skuInput.value = data.product_sku;
                    itemNoInput.value = data.product_sku.slice(-5);
                    descriptionInput.value = data.product_name;
                    serialInput.value = barcode.slice(-7);
                    quantityInput.value = 1;
                }
            })
            .catch(error => console.error("Fetch error:", error));
        }
    });
});
