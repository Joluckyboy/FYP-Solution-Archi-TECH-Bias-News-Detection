import { Link } from "react-router-dom";

const Header = () => {
	return (
		<div className="flex justify-between items-center h-16 px-4 shadow-md sticky top-0 z-50 bg-white">
			<Link to="/" className="m-2 pl-4 flex items-center">
				<img src="/checkmate.svg" alt="checkmatelogo" />
				<h2 className="ml-2 checkmate-gradient text-lg">CheckMate</h2>
			</Link>

      <div className="flex items-center gap-2">
        {/* <Link
          to="/dashboard"
          className="m-2 px-3 py-2 rounded-md hover:bg-gray-100 text-sm font-medium"
        >
          Dashboard
        </Link> */}

        <Link to="/games">
          <div className="m-2 pr-4">
            <img src="/game.svg" alt="gamelogo" className="w-9 h-9"/>
          </div>
        </Link>

        <Link to="/how-it-works">
          <div className="m-2 pr-4">
            <img src="/how-it-works.svg" alt="howitworkslogo" className="w-9 h-9"/>
          </div>
        </Link>

      </div>
		</div>
	);
};

export default Header;

