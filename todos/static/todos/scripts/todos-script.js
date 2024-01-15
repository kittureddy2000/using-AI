function formatDate(dateString) {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const date = new Date(dateString);
    const day = date.getDate();
    const monthIndex = date.getMonth();
    const year = date.getFullYear().toString().substr(-2); // Get last two digits of the year
    const formattedDate = `${day}-${months[monthIndex]}-${year}`;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (date < today) {
        // If the date is in the past, wrap it in a span with text-danger class
        return `<span class="text-danger">${formattedDate}</span>`;
    } else {
        return formattedDate;
    }
  }