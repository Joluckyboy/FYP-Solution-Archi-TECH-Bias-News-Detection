const PROD_HOST = "47.131.119.153";
const CLOUD_API = `http://${PROD_HOST}:8010`;
const CLOUD_ANALYZER = `http://${PROD_HOST}:8017`;
const CLOUD_BIAS = `http://${PROD_HOST}:9000`;
const LOCAL_API = "http://localhost:8010";
const LOCAL_ANALYZER = "http://localhost:8017";
const LOCAL_BIAS = "http://localhost:9000";

let _cachedAPI = null;
let _cachedAnalyzer = null;
let _cachedBias = null;

const detectBackend = async () => {
    if (_cachedAPI) return;

    // Try cloud first
    try {
        const res = await fetch(`${CLOUD_API}/`, { signal: AbortSignal.timeout(5000) });
        if (res.ok) {
            _cachedAPI = CLOUD_API;
            _cachedAnalyzer = CLOUD_ANALYZER;
            _cachedBias = CLOUD_BIAS;
            console.log("[Checkmate] Using cloud backend:", _cachedAPI);
            return;
        }
    } catch { /* cloud unavailable */ }

    // Fall back to localhost
    try {
        const res = await fetch(`${LOCAL_API}/`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            _cachedAPI = LOCAL_API;
            _cachedAnalyzer = LOCAL_ANALYZER;
            _cachedBias = LOCAL_BIAS;
            console.log("[Checkmate] Using local backend:", _cachedAPI);
            return;
        }
    } catch { /* local unavailable */ }

    throw new Error("No backend available (cloud and localhost both failed)");
};

const get_api = async () => {
    await detectBackend();
    return _cachedAPI;
};

const get_analyzer = async () => {
    await detectBackend();
    return _cachedAnalyzer;
};

const get_bias = async () => {
    await detectBackend();
    return _cachedBias;
};

export { get_analyzer, get_bias };
export default get_api;
