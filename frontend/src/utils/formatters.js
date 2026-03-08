export function formatPrice(price) {

  if (price === undefined || price === null) {
    return "-";
  }

  return Number(price).toFixed(2);

}

export function formatTime(timestamp) {

  if (!timestamp) {
    return "";
  }

  const date = new Date(timestamp);

  return date.toLocaleTimeString();

}

export function formatNumber(num) {

  if (num === undefined || num === null) {
    return "-";
  }

  return Number(num).toLocaleString();

}
