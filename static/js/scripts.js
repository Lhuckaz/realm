function copyMagnet(magnet) {
    navigator.clipboard.writeText(magnet).then(() => {
        const copyMessage = document.getElementById('copyMessage');
        // Show the message box
        copyMessage.classList.remove('error'); // Remove error class if present
        copyMessage.classList.add('show');     // Make it visible and fade in
        // Hide the message box after 3 seconds
        setTimeout(() => {
            copyMessage.classList.remove('show'); // Fade out
            // The 'visibility: hidden' transition handles the full hiding
        }, 3000); // 3 seconds timeout
    });
}
function sendToQB(link, is_series, season, item_title) {
    const messageBox = document.getElementById('messageBox');
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
                // Show the message box
                messageBox.classList.remove('error'); // Remove error class if present
                messageBox.classList.add('show');     // Make it visible and fade in
                // Hide the message box after 3 seconds
                setTimeout(() => {
                    messageBox.classList.remove('show'); // Fade out
                    // The 'visibility: hidden' transition handles the full hiding
                }, 3000); // 3 seconds timeout
            } else {
                console.error(data.message);
            }
        });
}