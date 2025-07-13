function updateButtonText(button, newText, isError = false) {
    const originalText = button.dataset.originalText;
    button.textContent = newText;
    button.disabled = true; // Disable button to prevent multiple clicks while message is shown

    // Store original background color to revert to it properly
    const originalBackgroundColor = getComputedStyle(button).backgroundColor;

    if (isError) {
        button.style.backgroundColor = '#f44336'; // Red for error
    } else {
        button.style.backgroundColor = '#4CAF50'; // Green for success
    }

    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false; // Re-enable the button
        // Revert button color to its original computed style
        button.style.backgroundColor = originalBackgroundColor;
    }, 3000); // Revert after 2 seconds
}

function copyMagnet(magnet, buttonElement) {
    navigator.clipboard.writeText(magnet).then(() => {
        updateButtonText(buttonElement, 'Copied!');
    }).catch(err => {
        console.error('Failed to copy magnet link: ', err);
        updateButtonText(buttonElement, 'Copy Failed!', true);
    });
}

// Unified function to send to qBittorrent for both movies and series
function sendToQB(link, is_series, season, item_title, imdb_id, buttonElement) {
    const requestBody = {
        magnet: link,
        is_series: is_series,
        imdb_id: imdb_id
    };

    // Only add season and item_title if it's a series
    if (is_series === 'True') { // Note: is_series comes as a string 'True' or 'False' from Jinja2
        requestBody.season = season;
        requestBody.item_title = item_title;
    }

    fetch("/send_to_qb", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                updateButtonText(buttonElement, 'Sent!');
            } else {
                console.error(data.message);
                updateButtonText(buttonElement, 'Send Failed!', true);
            }
        })
        .catch(error => {
            console.error('Error sending to qBittorrent:', error);
            updateButtonText(buttonElement, 'Error!', true);
        });
}