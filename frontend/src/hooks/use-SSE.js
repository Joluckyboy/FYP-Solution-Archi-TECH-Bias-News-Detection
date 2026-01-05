

const createSSEConnection = (API_URL, newsId, onMessage) => {
    if (!newsId) return null;

    const eventSource = new EventSource(`${API_URL}/application/stream_news?news_id=${newsId}`);

    eventSource.onmessage = (event) => {
        console.log("Update received:", event.data);
        onMessage(JSON.parse(event.data));
    };

    eventSource.onerror = () => {
        console.error("SSE connection error");
        eventSource.close();
    };

    return eventSource;
};


export default createSSEConnection;