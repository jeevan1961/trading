let socket = null;

export function connectWebSocket(onMessage) {

  socket = new WebSocket("ws://localhost:8000/stream");

  socket.onopen = () => {
    console.log("WebSocket connected");
  };

  socket.onmessage = (event) => {

    try {

      const data = JSON.parse(event.data);

      if (onMessage) {
        onMessage(data);
      }

    } catch (err) {
      console.error("WebSocket parse error:", err);
    }

  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
  };

  socket.onclose = () => {
    console.log("WebSocket closed");
  };

}

export function closeWebSocket() {

  if (socket) {
    socket.close();
    socket = null;
  }

}
