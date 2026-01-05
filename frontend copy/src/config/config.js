import axios from "axios";

const LOCAL_API_URL = "http://localhost:8010";
const GAMES_API_URL = "https://service.chfwhitehats2024.games";

let API_URL = LOCAL_API_URL;

const get_api = async () => {
    try {
        // console.log(GAMES_API_URL);
        await axios.get(GAMES_API_URL + "/application");
        API_URL = GAMES_API_URL;
    } catch (error) {
        API_URL = LOCAL_API_URL;
    }
    return API_URL;
};

export default get_api;