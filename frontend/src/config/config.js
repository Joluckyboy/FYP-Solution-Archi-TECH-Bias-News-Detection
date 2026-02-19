const PROD_HOST = "47.131.119.153";
const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const HOST = isLocal ? "localhost" : PROD_HOST;

const API_URL = `http://${HOST}:8010`;
const ANALYZER_URL = `http://${HOST}:8017`;

const get_api = async () => {
    return API_URL;
};

export { ANALYZER_URL };
export default get_api;
