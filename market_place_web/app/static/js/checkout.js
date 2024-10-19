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
    cartContainer.innerHTML = '<h2 class="section-title">Your Shopping Cart</h2>';

    if (products.length === 0) {
        cartContainer.innerHTML += '<p class="empty-cart">Your cart is empty. Start shopping!</p>';
        return;
    }

    let cartList = document.createElement('ul');
    cartList.classList.add('cart-list');

    products.forEach(product => {
        let quantity = cart[product.product_id];
        let cartItem = document.createElement('li');
        cartItem.classList.add('cart-item');
        cartItem.setAttribute('data-product-id', product.product_id);

        // Check if price exists and is a number
        let price = 0;
        if (product.prices && Array.isArray(product.prices) && product.prices.length > 0) {
            price = parseFloat(product.prices[0].price);
        } else if (typeof product.price === 'number') {
            price = product.price;
        }

        if (isNaN(price)) {
            console.error('Invalid price for product:', product);
            price = 0;
        }

        let totalPrice = price * quantity;

        cartItem.innerHTML = `
            <div class="cart-item-image">
                <img src="${product.image_url || '/path/to/placeholder-image.jpg'}" alt="${product.name}">
            </div>
            <div class="cart-item-details">
                <h3 class="cart-item-name">${product.name}</h3>
                <p class="cart-item-price">€${totalPrice.toFixed(2)}</p>
                <p class="cart-item-unit-price">Unit Price: €${price.toFixed(2)}</p>
                <div class="quantity-controls">
                    <button class="quantity-btn quantity-decrease" data-product-id="${product.product_id}">-</button>
                    <span class="quantity-display">${quantity}</span>
                    <button class="quantity-btn quantity-increase" data-product-id="${product.product_id}">+</button>
                </div>
            </div>
            <button class="remove-item" data-product-id="${product.product_id}">Remove</button>
        `;

        cartList.appendChild(cartItem);
    });

    cartContainer.appendChild(cartList);

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

// Additional CSS styles
const styles = `
    .cart-list {
        list-style-type: none;
        padding: 0;
    }
    .cart-item {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #e0e0e0;
        padding: 15px 0;
    }
    .cart-item-image {
        width: 80px;
        height: 80px;
        margin-right: 15px;
    }
    .cart-item-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .cart-item-details {
        flex-grow: 1;
    }
    .cart-item-name {
        margin: 0 0 5px 0;
    }
    .cart-item-price {
        font-weight: bold;
        color: #e74c3c;
    }
    .cart-item-unit-price {
        font-size: 0.9em;
        color: #7f8c8d;
    }
    .quantity-controls {
        display: flex;
        align-items: center;
        margin-top: 10px;
    }
    .quantity-btn {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 5px 10px;
        cursor: pointer;
    }
    .quantity-display {
        margin: 0 10px;
    }
    .remove-item {
        background-color: #e74c3c;
        color: white;
        border: none;
        padding: 5px 10px;
        cursor: pointer;
    }
    .empty-cart {
        text-align: center;
        font-style: italic;
        color: #7f8c8d;
    }
`;

// Apply the styles
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);


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
        
        // Remove item from display without full refresh
        let itemToRemove = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
        if (itemToRemove) {
            itemToRemove.remove();
        }
    
        // If cart is now empty, update display
        if (Object.keys(cart).length === 0) {
            let cartContainer = document.getElementById('cartContainer');
            cartContainer.innerHTML = '<p class="empty-cart">Your cart is empty. Start shopping!</p>';
            document.getElementById('totalCostContainer').innerHTML = '';
        } else {
            // Recalculate totals
            fetch('/get_cart_products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ cart: cart })
            })
            .then(response => response.json())
            .then(data => {
                calculateTotalCosts(data.products, data.stores);
            })
            .catch(error => {
                console.error('Error fetching cart products:', error);
            });
        }
    }
    function displayComparisonTable(productData, stores, totals) {
        let totalCostContainer = document.getElementById('totalCostContainer');
        totalCostContainer.innerHTML = '<h2 class="table-title">Compare Supermarkets</h2>';
    
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
    
        // Last column for quantity
        let quantityHeader = document.createElement('th');
        quantityHeader.textContent = 'Quantity';
        headerRow.appendChild(quantityHeader);
    
        thead.appendChild(headerRow);
        table.appendChild(thead);
    
        // Create table body with product rows
        let tbody = document.createElement('tbody');
    
        let totalItems = Object.keys(productData).length;
        let availableItems = {};
    
        Object.values(productData).forEach((product, index) => {
            let tr = document.createElement('tr');
            tr.classList.add(index % 2 === 0 ? 'even-row' : 'odd-row');
    
            // Product name cell
            let productCell = document.createElement('td');
            productCell.textContent = product.name;
            tr.appendChild(productCell);
    
            // Availability per supermarket
            stores.forEach(store => {
                let td = document.createElement('td');
                let isAvailable = product.availability[store];
    
                let icon = document.createElement('span');
                icon.classList.add('availability-icon');
                
                if (isAvailable) {
                    icon.innerHTML = '✓';
                    icon.classList.add('available');
                    availableItems[store] = (availableItems[store] || 0) + 1;
                } else {
                    icon.innerHTML = '×';
                    icon.classList.add('unavailable');
                }
    
                td.appendChild(icon);
                tr.appendChild(td);
            });
    
            // Quantity column
            let quantityCell = document.createElement('td');
            quantityCell.textContent = product.quantity;
            tr.appendChild(quantityCell);
    
            tbody.appendChild(tr);
        });
    
        // Add availability summary row
        let availabilityRow = document.createElement('tr');
        availabilityRow.classList.add('availability-summary');
    
        let availabilitySummaryCell = document.createElement('td');
        availabilitySummaryCell.textContent = 'Available Items';
        availabilityRow.appendChild(availabilitySummaryCell);
    
        stores.forEach(store => {
            let td = document.createElement('td');
            td.textContent = `${availableItems[store] || 0} / ${totalItems}`;
            availabilityRow.appendChild(td);
        });
    
        let emptyQuantityCell = document.createElement('td');
        availabilityRow.appendChild(emptyQuantityCell);
    
        tbody.appendChild(availabilityRow);
    
        // Add total cost row
        let totalRow = document.createElement('tr');
        totalRow.classList.add('total-row');
    
        // First cell for "Total Cost"
        let totalLabelCell = document.createElement('td');
        totalLabelCell.textContent = 'Total Cost';
        totalRow.appendChild(totalLabelCell);
    
        // Find the lowest non-zero total cost
        let lowestTotal = Math.min(...Object.values(totals).filter(total => total > 0));
    
        stores.forEach(store => {
            let td = document.createElement('td');
            let totalCost = totals[store];
    
            td.textContent = `€${totalCost.toFixed(2)}`;
    
            if (totalCost === lowestTotal && totalCost > 0) {
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
    
        // Add CSS styles
        const styles = `
            .table-title {
                font-size: 28px;
                color: #2c3e50;
                margin-bottom: 25px;
                text-align: center;
                font-weight: 600;
            }
            .comparison-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 0 25px rgba(0, 0, 0, 0.1);
                font-family: Arial, sans-serif;
            }
            .comparison-table th, .comparison-table td {
                padding: 18px;
                text-align: center;
                border-bottom: 1px solid #e0e0e0;
            }
            .comparison-table thead {
                background-color: #3498db;
                color: white;
            }
            .comparison-table th {
                font-weight: bold;
                text-transform: uppercase;
                font-size: 14px;
            }
            .store-logo {
                max-width: 100px;
                max-height: 50px;
                transition: transform 0.3s ease;
            }
            .store-logo:hover {
                transform: scale(1.1);
            }
            .even-row {
                background-color: #ffffff;
            }
            .odd-row {
                background-color: #f9f9f9;
            }
            .availability-icon {
                font-size: 22px;
                font-weight: bold;
            }
            .available {
                color: #2ecc71;
            }
            .unavailable {
                color: #e74c3c;
            }
            .total-row {
                font-weight: bold;
                background-color: #ecf0f1;
                font-size: 18px;
            }
            .lowest-total {
                color: #27ae60;
                font-weight: bold;
                position: relative;
            }
            .lowest-total::after {
                content: '★';
                position: absolute;
                top: -5px;
                right: -5px;
                font-size: 14px;
                color: #f39c12;
            }
            .availability-summary {
                background-color: #f2f2f2;
                font-weight: bold;
            }
     
            @media (max-width: 768px) {
                .comparison-table {
                    font-size: 14px;
                }
                .comparison-table th, .comparison-table td {
                    padding: 10px;
                }
                .store-logo {
                    max-width: 60px;
                    max-height: 30px;
                }
            }
        `;
    
        const styleSheet = document.createElement("style");
        styleSheet.type = "text/css";
        styleSheet.innerText = styles;
        document.head.appendChild(styleSheet);
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