// Add manufacturer search functionality and input correlation

document.addEventListener('DOMContentLoaded', () => {
    const manufacturerSelect = document.getElementById('manufacturer');
    const brandInput = document.getElementById('brand');
    const itemNoInput = document.getElementById('item-no');
    const skuInput = document.getElementById('sku');

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

    // Bind the brand input to search manufacturers
    brandInput.addEventListener('input', (e) => {
        searchManufacturers(e.target.value);
    });
});
