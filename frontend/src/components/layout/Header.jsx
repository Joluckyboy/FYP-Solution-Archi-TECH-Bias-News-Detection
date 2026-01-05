import { Link } from "react-router-dom";

const Header = () => {
	return (
		<div className="flex justify-between items-center h-16 px-4 shadow-md sticky top-0 z-50 bg-white">
			<Link to="/" className="m-2 pl-4 flex items-center">
				<img src="/checkmate.svg" alt="checkmatelogo" />
				<h2 className="ml-2 checkmate-gradient text-lg">CheckMate</h2>
			</Link>
            <Link to="/games">
                <div className="m-2 pr-4">
                    <img src="/game.svg" alt="gamelogo" />
                </div>
			</Link>
		</div>
	);
};

export default Header;
