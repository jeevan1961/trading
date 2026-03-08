let socket = null;

export function connectWebSocket(onMessage) {

  socket = new WebSocket(import.meta.env.VITE_WS_URL);

  socket.onopen = () => {
    console.log("WebSocket connected");
  };

  socket.onmessage = (event) => {

    const data = JSON.parse(event.data);

    if (onMessage) {
      onMessage(data);
    }

  };

}

export function closeWebSocket() {

  if (socket) {
    socket.close();
    socket = null;
  }

}
