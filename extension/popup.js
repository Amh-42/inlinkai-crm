const saveBtn = document.getElementById('saveBtn');
const status = document.getElementById('status');

// Disable button initially if not on a LinkedIn profile page
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const url = tabs[0].url;
    if (!url || !url.includes('linkedin.com/in/')) {
        saveBtn.disabled = true;
        status.textContent = 'Not a LinkedIn profile page.';
    }
});

saveBtn.addEventListener('click', async () => {
    saveBtn.disabled = true;
    status.textContent = 'Scraping...';

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab.url || !tab.url.includes('linkedin.com/in/')) {
             status.textContent = 'Error: Not a LinkedIn profile page.';
             saveBtn.disabled = false; // Re-enable if needed
             return;
        }

        // Inject the content script to scrape and send data
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
            // Alternatively, inject a function directly:
            // func: scrapeAndSendData, // Define scrapeAndSendData function here or in content.js
        });

         // Content script now handles sending data and feedback.
         // We can listen for a message back if needed, but for simplicity,
         // we assume content.js will update status or just finish.
         // Let's set a final message here after a short delay.
         setTimeout(() => {
             // Note: We don't know for sure if it succeeded from here
             // without message passing from content script.
             status.textContent = 'Attempted save. Check backend.';
             saveBtn.disabled = false;
         }, 2000); // Adjust delay as needed


    } catch (error) {
        console.error("Error initiating scraping:", error);
        status.textContent = `Error: ${error.message}`;
        saveBtn.disabled = false;
    }
});

// Optional: Listen for messages from content script for better feedback
// chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//     if (message.action === "scrape_status") {
//         status.textContent = message.text;
//         saveBtn.disabled = message.disableButton;
//     }
// });