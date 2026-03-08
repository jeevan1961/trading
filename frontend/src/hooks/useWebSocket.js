import { useEffect } from "react";
import { connectWebSocket, closeWebSocket } from "../services/websocket";

export default function useWebSocket(onMessage) {

  useEffect(() => {

    connectWebSocket(onMessage);

    return () => {
      closeWebSocket();
    };

  }, []);

}
