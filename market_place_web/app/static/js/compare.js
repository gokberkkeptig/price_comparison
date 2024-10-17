$(document).ready(function() {
    function recalculateBestPrice() {
        let cheapestPrice = Infinity;
        let cheapestProductId = null;

        // Iterate through each product card to find the cheapest price
        $('.product-card').each(function() {
            const priceText = $(this).find('.attribute-value').first().text().trim().replace('€', '');
            const price = parseFloat(priceText);
            const productId = $(this).find('.remove-button').data('product-id');

            if (price < cheapestPrice) {
                cheapestPrice = price;
                cheapestProductId = productId;
            }
        });

        // Remove existing best price badges
        $('.best-price-badge').remove();

        // Remove the 'cheapest-product' class from all cards
        $('.product-card').removeClass('cheapest-product');

        // Add the 'cheapest-product' class and best price badge to the new cheapest product
        if (cheapestProductId !== null) {
            const cheapestCard = $('.remove-button[data-product-id="' + cheapestProductId + '"]').closest('.product-card');
            cheapestCard.addClass('cheapest-product');
            cheapestCard.prepend('<span class="best-price-badge">Best Price</span>');
        }
    }

    // Initial best price calculation
    recalculateBestPrice();

    // Remove button click handler
    $('.remove-button').click(function() {
        const productId = $(this).data('product-id');
        // Remove the product card
        $(this).closest('.product-card').parent().remove();

        // Recalculate the best price after removal
        recalculateBestPrice();

        // If no more products, redirect to home page
        if ($('.product-card').length === 0) {
            window.location.href = "{{ url_for('home') }}";
        }
    });
});