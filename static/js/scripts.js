function updateButtonText(button, newText, isError = false) {
    const originalText = button.dataset.originalText;
    button.textContent = newText;
    button.disabled = true; // Disable button to prevent multiple clicks while message is shown

    // You might want to add a class for error styling if needed
    if (isError) {
        button.style.backgroundColor = '#f44336'; // Example: change color for error
    } else {
        button.style.backgroundColor = '#4CAF50'; // Example: change color for success
    }


    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false; // Re-enable the button
        // Revert button color to original if you changed it for success/error
        button.style.backgroundColor = ''; // Clear inline style
    }, 2000); // Revert after 2 seconds
}

function copyMagnet(magnet, buttonElement) {
    navigator.clipboard.writeText(magnet).then(() => {
        updateButtonText(buttonElement, 'Copied!');
    }).catch(err => {
        console.error('Failed to copy magnet link: ', err);
        updateButtonText(buttonElement, 'Copy Failed!', true);
    });
}

function sendToQB(link, is_series, season, item_title, buttonElement) {
    fetch("/send_to_qb", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            magnet: link,
            is_series: is_series,
            season: season,
            item_title: item_title
        })
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
function sendMovieToQB(link, is_series, buttonElement) {
    fetch("/send_to_qb", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            magnet: link,
            is_series: is_series,
        })
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