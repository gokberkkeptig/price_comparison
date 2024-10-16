let cart;

document.getElementById('clearCartButton').addEventListener('click', function() {
    if (confirm('Are you sure you want to clear your cart?')) {
        localStorage.removeItem('cart');
        window.location.reload();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart
    cart = JSON.parse(localStorage.getItem('cart')) || {};

    // Initial cart display
    refreshCart();
});

function refreshCart() {
    // If cart is empty
    if (Object.keys(cart).length === 0) {
        document.getElementById('cartContainer').innerHTML = '<p>Your cart is empty.</p>';
        document.getElementById('totalCostContainer').innerHTML = '';
        return;
    }

    // Fetch product data from the server
    fetch('/get_cart_products', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ cart: cart })
    })
    .then(response => response.json())
    .then(data => {
        displayCartItems(data.products);
        calculateTotalCosts(data.products, data.stores);
    })
    .catch(error => {
        console.error('Error fetching cart products:', error);
    });
}

function displayCartItems(products) {
    let cartContainer = document.getElementById('cartContainer');
    cartContainer.innerHTML = '';

    products.forEach(product => {
        let quantity = cart[product.product_id];
        let productDiv = document.createElement('div');
        productDiv.classList.add('cart-item');

        productDiv.innerHTML = `
            <img src="${product.image_url}" alt="${product.name}" class="cart-item-image">
            <div class="cart-item-details">
                <h3>${product.name}</h3>
                <div class="quantity-controls">
                    <button class="quantity-decrease" data-product-id="${product.product_id}">-</button>
                    <span class="quantity-display">${quantity}</span>
                    <button class="quantity-increase" data-product-id="${product.product_id}">+</button>
                </div>
                <button class="remove-item btn btn-link" data-product-id="${product.product_id}">Remove</button>
            </div>
        `;

        cartContainer.appendChild(productDiv);
    });

    // Add event listeners for quantity controls and remove buttons
    addCartEventListeners();
}

function addCartEventListeners() {
    // Event listeners for increase quantity
    const increaseButtons = document.querySelectorAll('.quantity-increase');
    increaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            increaseQuantity(productId);
        });
    });

    // Event listeners for decrease quantity
    const decreaseButtons = document.querySelectorAll('.quantity-decrease');
    decreaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            decreaseQuantity(productId);
        });
    });

        // Event listeners for remove item
        const removeButtons = document.querySelectorAll('.remove-item');
        removeButtons.forEach(button => {
            button.addEventListener('click', function() {
                const productId = this.getAttribute('data-product-id');
                removeItemFromCart(productId);
            });
        });
    }

    function increaseQuantity(productId) {
        // Increase quantity in cart
        cart[productId] += 1;
        localStorage.setItem('cart', JSON.stringify(cart));
        // Refresh UI
        refreshCart();
    }

    function decreaseQuantity(productId) {
        // Decrease quantity in cart
        if (cart[productId] > 1) {
            cart[productId] -= 1;
        } else {
            // If quantity is 1, remove the item
            delete cart[productId];
        }
        localStorage.setItem('cart', JSON.stringify(cart));
        // Refresh UI
        refreshCart();
    }

    function removeItemFromCart(productId) {
        // Remove item from cart
        delete cart[productId];
        localStorage.setItem('cart', JSON.stringify(cart));
        // Refresh UI
        refreshCart();
    }
    function displayComparisonTable(productData, stores, totals) {
        let totalCostContainer = document.getElementById('totalCostContainer');
        totalCostContainer.innerHTML = '<h3>Compare Supermarkets</h3>';
    
        // Create table
        let table = document.createElement('table');
        table.classList.add('comparison-table');
    
        // Create table header with supermarket logos
        let thead = document.createElement('thead');
        let headerRow = document.createElement('tr');
    
        // First header cell for "Products"
        let productHeader = document.createElement('th');
        productHeader.textContent = 'Products';
        headerRow.appendChild(productHeader);
    
        // Add supermarket columns
        stores.forEach(store => {
            let th = document.createElement('th');
            let logoImg = document.createElement('img');
            logoImg.src = `/static/logos/${store.toLowerCase().replace(' ', '_')}.jpeg`;
            logoImg.alt = store;
            logoImg.classList.add('store-logo');
    
            th.appendChild(logoImg);
            headerRow.appendChild(th);
        });
    
        // Last column for total cost per product (optional)
        let totalProductHeader = document.createElement('th');
        totalProductHeader.textContent = 'Quantity';
        headerRow.appendChild(totalProductHeader);
    
        thead.appendChild(headerRow);
        table.appendChild(thead);
    
        // Create table body with product rows
        let tbody = document.createElement('tbody');
    
        Object.values(productData).forEach(product => {
            let tr = document.createElement('tr');
    
            // Product name cell
            let productCell = document.createElement('td');
            productCell.textContent = product.name;
            tr.appendChild(productCell);
    
            // Availability per supermarket
            stores.forEach(store => {
                let td = document.createElement('td');
                let isAvailable = product.availability[store];
    
                if (isAvailable) {
                    td.innerHTML = '&#10003;'; // Checkmark symbol
                    td.classList.add('available');
                } else {
                    td.innerHTML = '&#10007;'; // Cross symbol
                    td.classList.add('unavailable');
                }
    
                tr.appendChild(td);
            });
    
            // Quantity column (optional)
            let quantityCell = document.createElement('td');
            quantityCell.textContent = product.quantity;
            tr.appendChild(quantityCell);
    
            tbody.appendChild(tr);
        });
    
        // Add total cost row
        let totalRow = document.createElement('tr');
        totalRow.classList.add('total-row');
    
        // First cell for "Total Cost"
        let totalLabelCell = document.createElement('td');
        totalLabelCell.textContent = 'Total Cost';
        totalRow.appendChild(totalLabelCell);
    
        // Find the lowest total cost to highlight the cheapest supermarket
        let lowestTotal = Math.min(...Object.values(totals));
    
        stores.forEach(store => {
            let td = document.createElement('td');
            let totalCost = totals[store];
    
            td.textContent = `€${totalCost.toFixed(2)}`;
    
            if (totalCost === lowestTotal) {
                td.classList.add('lowest-total');
            }
    
            totalRow.appendChild(td);
        });
    
        // Empty cell for alignment
        let emptyCell = document.createElement('td');
        totalRow.appendChild(emptyCell);
    
        tbody.appendChild(totalRow);
        table.appendChild(tbody);
        totalCostContainer.appendChild(table);
    }
    

    function calculateTotalCosts(products, stores) {
        let totals = {};
        let productData = {};
    
        // Initialize totals
        stores.forEach(store => {
            totals[store] = 0;
        });
    
        // Build product data
        products.forEach(product => {
            let quantity = cart[product.product_id];
    
            // Abbreviate product name if it's too long
            let productName = product.name.length > 50 ? product.name.substring(0, 50) + '...' : product.name;
    
            // Initialize product entry
            productData[product.product_id] = {
                name: productName,
                quantity: quantity,
                availability: {}
            };
    
            stores.forEach(store => {
                // Find if the product is available at this store
                let priceInfo = product.prices.find(p => p.store === store);
    
                if (priceInfo) {
                    // Product is available
                    productData[product.product_id].availability[store] = true;
    
                    // Update total cost
                    totals[store] += priceInfo.price * quantity;
                } else {
                    // Product is not available
                    productData[product.product_id].availability[store] = false;
                }
            });
        });
    
        displayComparisonTable(productData, stores, totals);
    }
    

    function displayTotalCosts(totals, storeItemAvailability) {
        let totalCostContainer = document.getElementById('totalCostContainer');
        totalCostContainer.innerHTML = '<h3>Total Cost per Supermarket:</h3>';

        // Convert totals object to an array and sort by total cost
        let sortedTotals = Object.keys(totals).map(store => {
            return { store: store, total: totals[store] };
        }).sort((a, b) => a.total - b.total);

        // Find the lowest total cost
        let lowestTotal = sortedTotals[0].total;

        // Create a table
        let table = document.createElement('table');
        table.classList.add('totals-table');

        // Table header
        let thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Supermarket</th>
                <th>Total Cost</th>
                <th>Available Items</th>
                <th>Unavailable Items</th>
            </tr>
        `;
        table.appendChild(thead);

        // Table body
        let tbody = document.createElement('tbody');

        sortedTotals.forEach(storeData => {
            let store = storeData.store;
            let totalCost = storeData.total.toFixed(2);
            let availableItems = storeItemAvailability[store].available;
            let unavailableItems = storeItemAvailability[store].unavailable;

            // Create table row
            let tr = document.createElement('tr');

            // Highlight the row if it's the cheapest
            if (storeData.total === lowestTotal) {
                tr.classList.add('lowest-total');
            }

            tr.innerHTML = `
                <td>${store}</td>
                <td>€${totalCost}</td>
                <td>${availableItems.length}</td>
                <td>${unavailableItems.length}</td>
            `;

            // Add tooltip or modal for item details
            tr.addEventListener('click', () => {
                showStoreDetails(store, availableItems, unavailableItems);
            });

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        totalCostContainer.appendChild(table);
    }

    function showStoreDetails(store, availableItems, unavailableItems) {
        // Create a modal or use an existing modal element
        let modal = document.getElementById('storeDetailsModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'storeDetailsModal';
            modal.classList.add('modal');
            document.body.appendChild(modal);
        }

        // Modal content
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close-button">&times;</span>
                <h2>${store} - Details</h2>
                <h3>Available Items:</h3>
                <ul>
                    ${availableItems.map(item => `<li>${item.name} - €${item.price.toFixed(2)} x ${item.quantity}</li>`).join('')}
                </ul>
                <h3>Unavailable Items:</h3>
                <ul>
                    ${unavailableItems.map(itemName => `<li>${itemName}</li>`).join('')}
                </ul>
            </div>
        `;

        // Show the modal
        modal.style.display = 'block';

        // Close button functionality
        modal.querySelector('.close-button').addEventListener('click', () => {
            modal.style.display = 'none';
        });

        // Close modal when clicking outside the content
        window.addEventListener('click', (event) => {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        });
    }